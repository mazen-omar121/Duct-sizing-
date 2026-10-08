"""Extract isolated vector symbols from the user-supplied CAD PDF export.

This is a drafting reference, not the Administration design basis. Run with
--reference-pdf pointing to HVAC LAYOUT,SCHEMATIC & SECTIONS(2).pdf.
The resulting JSON is included so the drawing builder does not need the
reference project's complete PDF or a DWG converter.
"""
from pathlib import Path
import argparse, json, math
import fitz

ap = argparse.ArgumentParser()
ap.add_argument('--reference-pdf', required=True)
ap.add_argument('--output', default=str(Path(__file__).resolve().parents[1] / 'inputs/Reference_symbol_geometry.json'))
args = ap.parse_args()
page = fitz.open(args.reference_pdf)[1]
specs = {
    'HVAC_VCD': ((1849.0,1550.8,1891.1,1555.5),(1869.26,1553.16),39.96,4.32),
    'HVAC_MD': ((1849.0,944.8,1890.3,949.5),(1867.22,947.16),35.88,4.32),
    'HVAC_MFD': ((1848.8,969.3,1892.7,976.0),(1867.16,972.66),36.24,6.36),
    'HVAC_EH': ((1849.7,492.5,1887.5,501.6),(1867.40,497.04),35.04,8.64),
    'HVAC_SILENCER': ((1852.5,1225.3,1885.2,1245.1),(1868.84,1235.22),32.16,19.32),
}

def key(rgb):
    if rgb is None:return 'SYM'
    if max(rgb)-min(rgb)<.05:return 'DIM' if sum(rgb)/3>.15 else 'SYM'
    if rgb[2]>.7 and rgb[0]<.2:return 'RA'
    if rgb[0]>.7 and rgb[1]<.1:return 'FLOW'
    return 'EA'

symbols = {}
for name,(crop,origin,cross,axial) in specs.items():
    rect = fitz.Rect(crop); scale=600/cross
    # Horizontal span in the reference is the blade span. Our block base
    # axis is X (duct airflow); rotate that span into local Y.
    def xy(p):return [round((p.y-origin[1])*scale,4),round(-(p.x-origin[0])*scale,4)]
    ops=[]
    for draw in page.get_drawings():
        if not rect.contains(draw['rect']):continue
        if draw['fill'] and min(draw['fill'])>.99:continue
        paths=[]; path=[]
        def append(a,b):
            if path and math.hypot(a.x-path[-1].x,a.y-path[-1].y)>.04:
                paths.append(path.copy());path.clear()
            if not path:path.append(a)
            path.append(b)
        for item in draw['items']:
            if item[0]=='l':append(item[1],item[2])
            elif item[0]=='re':
                if path:paths.append(path.copy());path.clear()
                r=item[1];paths.append([r.tl,r.tr,r.br,r.bl,r.tl])
            elif item[0]=='c':
                a,b,c,d=item[1:]
                for i in range(16):
                    u=i/16;v=(i+1)/16
                    def q(t):
                        o=1-t
                        return fitz.Point(o**3*a.x+3*o*o*t*b.x+3*o*t*t*c.x+t**3*d.x,o**3*a.y+3*o*o*t*b.y+3*o*t*t*c.y+t**3*d.y)
                    append(q(u),q(v))
        if path:paths.append(path.copy())
        for path in paths:
            if len(path)<2:continue
            pts=[xy(p) for p in path]
            if all(math.hypot(p[0]-pts[0][0],p[1]-pts[0][1])<.1 for p in pts):continue
            filled=bool(draw['fill'])
            ops.append({'points':pts,'kind':key(draw['fill'] if filled else draw['color']),
                        'fill':filled,'closed':filled or draw.get('closePath',False),
                        'width':0 if filled else max(5,draw['width']*scale)})
    symbols[name]={'ops':ops,'core_axial_mm':round(axial*scale,4),'core_cross_mm':600}

out={'source':'D-113391 CAD drawing family / user-supplied PDF export, sheet 2 legend',
     'use':'Symbol geometry only; reference project technical data not adopted',
     'symbols':symbols}
Path(args.output).write_text(json.dumps(out,indent=2))
print(json.dumps({k:len(v['ops']) for k,v in symbols.items()}))
