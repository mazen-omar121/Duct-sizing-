"""HVAC plan drawing generator. Model coordinates and duct dimensions are millimetres."""
import io
import csv
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import ezdxf
from flask import Flask, jsonify, render_template, request, send_file

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 256 * 1024
ROOT = Path(__file__).resolve().parent
ADMIN_SOURCE = ROOT / 'projects' / 'administration_rev09'
ADMIN_OUTPUT = ROOT / 'generated' / 'administration'
SAMPLE = {
    'title': 'Supply air plan',
    'routes': [
        {'name': 'SA-01', 'width': 600, 'height': 400, 'flow': 900,
         'points': [[0, 0], [5000, 0], [5000, 3500], [9000, 3500]]},
        {'name': 'SA-02', 'width': 300, 'height': 250, 'flow': 250,
         'points': [[2500, 0], [2500, -3000], [6000, -3000]]},
    ],
    'equipment': [{'name': 'AHU-01', 'x': -1500, 'y': -500, 'width': 1500, 'depth': 1000}],
}


def number(value, label, low=-1000000, high=1000000):
    if isinstance(value, bool):
        raise ValueError(f'{label} must be a number')
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f'{label} must be a number') from None
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f'{label} must be between {low} and {high}')
    return value


def label(value, fallback):
    if value is None:
        value = fallback
    if not isinstance(value, str) or not value.strip() or len(value) > 80:
        raise ValueError('Labels must contain 1 to 80 characters')
    if any(ord(c) < 32 for c in value):
        raise ValueError('Labels cannot contain control characters')
    return value.strip()


def validate(data):
    if not isinstance(data, dict):
        raise ValueError('The drawing must be a JSON object')
    routes = data.get('routes')
    if not isinstance(routes, list) or not 1 <= len(routes) <= 40:
        raise ValueError('Provide 1 to 40 duct routes')
    result = {'title': label(data.get('title'), 'HVAC plan'), 'routes': [], 'equipment': []}
    for r in routes:
        if not isinstance(r, dict):
            raise ValueError('Each route must be an object')
        points = r.get('points')
        if not isinstance(points, list) or not 2 <= len(points) <= 100:
            raise ValueError('Each route needs 2 to 100 points')
        clean = []
        for p in points:
            if not isinstance(p, list) or len(p) != 2:
                raise ValueError('Each point must be [x, y]')
            clean.append([number(p[0], 'x'), number(p[1], 'y')])
        width = number(r.get('width'), 'Duct width', 50, 5000)
        for a, b in zip(clean, clean[1:]):
            if math.dist(a, b) < width:
                raise ValueError('Each duct segment must be at least its width long')
        # This first version uses orthogonal, constant-size routes and mitered elbows.
        for a, b in zip(clean, clean[1:]):
            if a[0] != b[0] and a[1] != b[1]:
                raise ValueError('Route segments must be horizontal or vertical')
        for a, b, c in zip(clean, clean[1:], clean[2:]):
            u = [b[i] - a[i] for i in (0, 1)]
            v = [c[i] - b[i] for i in (0, 1)]
            if u[0] * v[0] + u[1] * v[1] < 0:
                raise ValueError('Routes cannot reverse direction at a point')
        result['routes'].append({'name': label(r.get('name'), 'Duct'), 'width': width,
                                'height': number(r.get('height'), 'Duct height', 50, 5000),
                                'flow': number(r.get('flow', 0), 'Airflow', 0, 1000000),
                                'points': clean})
    equipment = data.get('equipment', [])
    if not isinstance(equipment, list) or len(equipment) > 40:
        raise ValueError('Provide at most 40 equipment items')
    for e in equipment:
        if not isinstance(e, dict):
            raise ValueError('Each equipment item must be an object')
        result['equipment'].append({'name': label(e.get('name'), 'Equipment'),
                                    'x': number(e.get('x'), 'Equipment x'),
                                    'y': number(e.get('y'), 'Equipment y'),
                                    'width': number(e.get('width'), 'Equipment width', 50, 10000),
                                    'depth': number(e.get('depth'), 'Equipment depth', 50, 10000)})
    return result


def outline(points, width):
    normals = []
    for a, b in zip(points, points[1:]):
        length = math.dist(a, b)
        normals.append((-(b[1] - a[1]) / length, (b[0] - a[0]) / length))
    sides = []
    for sign in (1, -1):
        side = []
        for i, p in enumerate(points):
            n = normals[min(i, len(normals) - 1)]
            if 0 < i < len(points) - 1:
                prev = normals[i - 1]
                divisor = 1 + prev[0] * n[0] + prev[1] * n[1]
                n = ((prev[0] + n[0]) / divisor, (prev[1] + n[1]) / divisor)
            side.append((p[0] + sign * width / 2 * n[0], p[1] + sign * width / 2 * n[1]))
        sides.append(side)
    return sides[0] + list(reversed(sides[1]))


def drawing(model):
    doc = ezdxf.new('R2018', setup=True)
    doc.units = ezdxf.units.MM
    for name, color in [('DUCT', 4), ('CENTERLINE', 8), ('EQUIPMENT', 3),
                        ('DIMENSIONS', 2), ('ANNOTATIONS', 7), ('FITTINGS', 6)]:
        doc.layers.new(name, dxfattribs={'color': color})
    space = doc.modelspace()
    points = [p for r in model['routes'] for p in r['points']]
    top = max(p[1] for p in points) + 1500
    left = min(p[0] for p in points)
    space.add_text(model['title'], dxfattribs={'height': 250, 'insert': (left, top), 'layer': 'ANNOTATIONS'})
    space.add_text('PLAN | mm | airflow L/s | width x height | mitered elbows',
                   dxfattribs={'height': 120, 'insert': (left, top - 350), 'layer': 'ANNOTATIONS'})
    for r in model['routes']:
        p = r['points']
        space.add_lwpolyline(outline(p, r['width']), close=True, dxfattribs={'layer': 'DUCT'})
        space.add_lwpolyline(p, dxfattribs={'layer': 'CENTERLINE', 'linetype': 'CENTER'})
        for a, b in zip(p, p[1:]):
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            velocity = r['flow'] * 1000 / (r['width'] * r['height'])
            text = f"{r['name']} {r['width']:g}x{r['height']:g} | {r['flow']:g} L/s | {velocity:.2f} m/s"
            space.add_text(text, dxfattribs={'height': 100, 'insert': (mid[0] + 100, mid[1] + 100), 'layer': 'ANNOTATIONS'})
            horizontal = a[1] == b[1]
            offset = r['width'] / 2 + 450
            base = (mid[0], mid[1] + offset) if horizontal else (mid[0] + offset, mid[1])
            space.add_linear_dim(base=base, p1=a, p2=b, angle=0 if horizontal else 90,
                                 dimstyle='EZDXF', dxfattribs={'layer': 'DIMENSIONS'},
                                 override={'dimtxt': 100, 'dimasz': 80, 'dimexo': 50, 'dimexe': 70}).render()
        for a, b, c in zip(p, p[1:], p[2:]):
            if (b[0] - a[0]) * (c[1] - b[1]) != (b[1] - a[1]) * (c[0] - b[0]):
                space.add_text('MITER ELBOW', dxfattribs={'height': 80, 'insert': (b[0] + 150, b[1] - r['width'] / 2 - 200), 'layer': 'FITTINGS'})
    for e in model['equipment']:
        x, y, w, d = (e[k] for k in ('x', 'y', 'width', 'depth'))
        space.add_lwpolyline([(x, y), (x + w, y), (x + w, y + d), (x, y + d)], close=True,
                            dxfattribs={'layer': 'EQUIPMENT'})
        space.add_text(e['name'], dxfattribs={'height': 120, 'insert': (x + 80, y + d / 2), 'layer': 'EQUIPMENT'})
    doc.set_modelspace_vport(height=max(10000, top - min(p[1] for p in points) + 1500),
                             center=((left + max(p[0] for p in points)) / 2, (top + min(p[1] for p in points)) / 2))
    return doc


def converter():
    configured = os.environ.get('DUCT_ODA_CONVERTER')
    return shutil.which(configured or 'ODAFileConverter')


def convert_dwg(source, engine):
    """Convert one DXF using fixed converter arguments; never invoke a shell."""
    with tempfile.TemporaryDirectory(prefix='duct-dwg-') as temp:
        src, dest = Path(temp) / 'input', Path(temp) / 'output'
        src.mkdir()
        dest.mkdir()
        shutil.copyfile(source, src / 'drawing.dxf')
        try:
            result = subprocess.run([engine, str(src), str(dest), 'ACAD2018', 'DWG', '0', '1', 'drawing.dxf'],
                                    capture_output=True, timeout=90, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise RuntimeError('The DWG engine could not run. Check the server converter installation.') from None
        path = dest / 'drawing.dwg'
        if result.returncode != 0 or not path.is_file() or path.stat().st_size < 100:
            raise RuntimeError('The DWG engine did not produce a drawing. Check its server installation.')
        payload = path.read_bytes()
        if payload[:6] != b'AC1032':
            raise RuntimeError('The converter output is not an AutoCAD 2018 DWG.')
        return payload


@app.get('/api/administration')
def administration():
    schedules = ADMIN_SOURCE / 'cad-package' / 'schedules'
    if not schedules.is_dir():
        return jsonify(error='Administration project inputs are not available'), 503
    with (schedules / 'Duct_sections.csv').open() as f:
        sections = list(csv.DictReader(f))
    with (schedules / 'Terminals.csv').open() as f:
        terminals = list(csv.DictReader(f))
    report_path = ADMIN_OUTPUT / 'drawing_validation.json'
    report = json.loads(report_path.read_text()) if report_path.is_file() else None
    return jsonify(revision=9, sections=len(sections), terminals=len(terminals),
                   supply_l_s=3697.80, assumed_return_l_s=3006.68,
                   outdoor_air_reference_l_s=420.70, implied_makeup_l_s=691.12,
                   report=report, ready=bool(report), dwg_available=bool(converter()),
                   holds=['Actual pressure balance and outdoor-air compliance remain unverified.',
                          'Levels, fitting losses, fan ESP and catalogue selections remain open.',
                          'This register cross-checks retained sizes; it does not select new duct sizes.'])


@app.get('/api/administration/export/<kind>')
def administration_export(kind):
    files = {'dxf': 'Administration_HVAC_Detailed_Layout.dxf',
             'pdf': 'Administration_Detailed_HVAC_Duct_Flow_Diagram.pdf',
             'mono': 'Administration_Detailed_HVAC_Duct_Flow_Diagram_Monochrome.pdf',
             'zip': 'Administration_HVAC_Rev09.zip',
             'xlsx': 'Administration_HVAC_Drawing_Registers_Rev09.xlsx',
             'dwg': 'Administration_HVAC_Detailed_Layout.dxf'}
    if kind not in files:
        return jsonify(error='Choose PDF, monochrome PDF, ZIP, XLSX, DXF or DWG'), 400
    path = ADMIN_OUTPUT / files[kind]
    if not path.is_file():
        return jsonify(error='Rebuild the Administration project first; see README.md'), 503
    if kind == 'dwg':
        engine = converter()
        if not engine:
            return jsonify(error='DWG export requires ODA File Converter. Configure DUCT_ODA_CONVERTER on the server.'), 503
        try:
            payload = convert_dwg(path, engine)
        except RuntimeError as error:
            return jsonify(error=str(error)), 502
        return send_file(io.BytesIO(payload), mimetype='application/octet-stream', as_attachment=True,
                         download_name='Administration_HVAC_Detailed_Layout.dwg')
    return send_file(path, as_attachment=True)


@app.get('/api/administration/overview')
def administration_overview():
    path = ADMIN_OUTPUT / 'Administration_HVAC_Overview.png'
    if not path.is_file():
        return jsonify(error='Rebuild the Administration project first'), 503
    return send_file(path, mimetype='image/png')


@app.get('/')
def index():
    return render_template('index.html')


@app.get('/api/status')
def status():
    return jsonify(dwg_available=bool(converter()), dwg_engine='ODA File Converter', units='mm')


@app.get('/api/sample')
def sample():
    return jsonify(SAMPLE)


@app.post('/api/preview')
def preview():
    model = validate(request.get_json())
    return jsonify(model=model, outlines=[outline(r['points'], r['width']) for r in model['routes']],
                   velocities=[r['flow'] * 1000 / (r['width'] * r['height']) for r in model['routes']])


@app.post('/api/export/<kind>')
def export(kind):
    if kind not in ('dxf', 'dwg'):
        return jsonify(error='Choose DXF or DWG'), 400
    model = validate(request.get_json())
    engine = converter() if kind == 'dwg' else None
    if kind == 'dwg' and not engine:
        return jsonify(error='DWG export requires ODA File Converter. Configure DUCT_ODA_CONVERTER on the server.'), 503
    with tempfile.TemporaryDirectory(prefix='duct-cad-') as temp:
        src, dest = Path(temp) / 'input', Path(temp) / 'output'
        src.mkdir()
        dest.mkdir()
        path = src / 'drawing.dxf'
        drawing(model).saveas(path)
        if kind == 'dwg':
            try:
                payload = convert_dwg(path, engine)
            except RuntimeError as error:
                return jsonify(error=str(error)), 502
        else:
            payload = path.read_bytes()
    return send_file(io.BytesIO(payload), mimetype='application/octet-stream', as_attachment=True,
                     download_name=f'hvac-plan.{kind}')


@app.errorhandler(ValueError)
def invalid(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(400)
def bad_request(error):
    return jsonify(error='Send valid JSON drawing data'), 400


@app.errorhandler(413)
def too_large(error):
    return jsonify(error='Drawing data exceeds 256 KB'), 413


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()
    app.run(host='127.0.0.1', port=args.port)
