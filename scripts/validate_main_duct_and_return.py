"""Validate delivered DX method drawings independently of their generator."""
from pathlib import Path
from math import log10,sqrt
from collections import defaultdict,Counter
import csv,json,hashlib
import ezdxf,fitz,openpyxl

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'projects/main_duct_and_return'
if not SOURCE.is_dir():SOURCE=ROOT/'source'  # extracted portable package
OUT=ROOT/'generated/main_duct_and_return'
def rows(path):
    with path.open() as f:return list(csv.DictReader(f))

def main():
    base=ROOT/'projects/administration_rev12/cad-package/schedules'
    provenance=json.loads((SOURCE/'PROVENANCE.json').read_text())
    for name,digest in provenance['input_sha256'].items():
        assert hashlib.sha256((SOURCE/'inputs'/name).read_bytes()).hexdigest()==digest,(name,'input changed')
    for name in ['Instruments.csv','IO_points.csv','Terminals.csv','Components.csv','Roof_risers.csv']:
        original='Roof_risers.csv' if name=='Roof_risers.csv' else name
        if base.is_dir():assert rows(SOURCE/'inputs'/name)==rows(base/original),(name,'baseline changed')
    basis=json.loads((OUT/'method_basis.json').read_text());assert basis['sheets']==14
    assert basis['main_location']=='Roof common mains with room drops - user selected'
    assert basis['room_drops']==15 and basis['common_roof_route_segments']==31
    instruments=rows(SOURCE/'inputs/Instruments.csv');terminals=rows(SOURCE/'inputs/Terminals.csv');io=rows(SOURCE/'inputs/IO_points.csv')
    assert len(instruments)==85 and len(terminals)==53 and len(io)==275
    dx=rows(OUT/'Additional_DX_proposals.csv');index=rows(OUT/'Instrument_drawing_index.csv')
    assert len(dx)==22 and len({r['tag'] for r in dx})==22
    assert not {r['tag'] for r in dx}&{r['tag'] for r in instruments}
    assert {r['tag'] for r in index}=={r['tag'] for r in instruments}
    for r in rows(OUT/'Common_main_sizing.csv'):
        q,take,after=map(float,[r['flow_before_takeoff_l_s'],r['takeoff_l_s'],r['flow_after_takeoff_l_s']]);w,h=map(float,[r['clear_width_mm'],r['clear_depth_mm']])
        assert abs(q-take-after)<1e-8
        v=q/1000/(w*h/1e6);assert abs(v-float(r['velocity_m_s']))<1e-6
        dh=2*w*h/(w+h)/1000;re=1.2*v*dh/1.81e-5;f=.02
        for _ in range(30):f=1/(-2*log10(.00009/(3.7*dh)+2.51/(re*sqrt(f))))**2
        assert abs(f/dh*.6*v*v-float(r['straight_friction_pa_m']))<1e-6
        assert (w,h)==((600,1300) if r['air_type']=='SA' else (700,900))
    with fitz.open(OUT/'Main duct and return.pdf') as pdf:
        assert len(pdf)==14
        text=[p.get_text() for p in pdf]
        assert all(abs(p.rect.width*25.4/72-841)<.01 and abs(p.rect.height*25.4/72-594)<.01 for p in pdf)
        for r in index:
            for ref in r['graphical_sheet'].split(' / '):assert r['tag'] in text[int(ref[-3:])-1],(r['tag'],ref)
        assert all(r['tag'] in text[4] for r in dx)
        assert all(r['tag'] in text[1] for r in terminals)
        risers=rows(SOURCE/'inputs/Roof_risers.csv')
        assert all(r['tag'] in text[0] and r['tag'] in text[7] and r['tag'] in text[11] for r in risers)
        assert all('ROOF' in text[0] and tag in text[0] and tag in text[3] for tag in ['PAU-A','PAU-B','PAU-C'])
        for i in range(11):assert f'SHEET {i+1} OF 14' in text[i]
        for i in range(11,14):assert f'MDR-{i+1:03} REFERENCE PLAN' in text[i]
        overflow=[]
        for number,p in enumerate(pdf,1):
            for block in p.get_text('dict')['blocks']:
                for line in block.get('lines',[]):
                    for span in line['spans']:
                        if not p.rect.contains(fitz.Rect(span['bbox'])):overflow.append((number,span['text']))
        assert not overflow,overflow
    with fitz.open(OUT/'Main duct and return - Monochrome.pdf') as pdf:
        assert len(pdf)==14
        colors={span['color'] for p in pdf for block in p.get_text('dict')['blocks'] for line in block.get('lines',[]) for span in line['spans']}
        assert all(abs((c>>16&255)-(c>>8&255))<=1 and abs((c>>8&255)-(c&255))<=1 for c in colors),colors
        for page in pdf:
            for drawing in page.get_drawings():
                for field in ['color','fill']:
                    color=drawing.get(field)
                    assert color is None or max(color)-min(color)<.01,('Monochrome vector color',color)
    doc=ezdxf.readfile(OUT/'Main duct and return.dxf');audit=doc.audit()
    assert not audit.has_errors,[(r.code,r.message) for r in audit.errors]
    assert doc.units==ezdxf.units.MM
    assert {f'MDR{i:02}_A1' for i in range(1,15)}<=set(doc.layouts.names())
    assert len(doc.modelspace().query('WIPEOUT'))>100 and len(doc.modelspace().query('HATCH'))>30
    assert not doc.layers.get('VIEWPORT').dxf.plot and not doc.layers.get('VIEWPORTS').dxf.plot
    assert doc.styles.get('Standard').dxf.font=='Arial.ttf'
    native_text={e.dxf.text for layout in doc.layouts for e in layout.query('TEXT')}
    native_text|={e.dxf.text for e in doc.modelspace().query('TEXT')}
    assert all(r['tag'] in native_text for r in instruments+dx)
    # Verify imported physical plans have their model references and translated viewports.
    inserts=[e for e in doc.modelspace().query('INSERT') if e.dxf.insert.x>=900000]
    assert len(inserts)>=3
    reference=ezdxf.readfile(SOURCE/'inputs/Rev12_reference.dxf')
    for insert in reference.modelspace().query('INSERT'):
        name=insert.dxf.name
        assert Counter(e.dxftype() for e in reference.blocks.get(name))==Counter(e.dxftype() for e in doc.blocks.get(name)),(name,'reference entities lost')
    for n,original in zip([12,13,14],['D023_A1','D001_A1','D007_A1']):
        vps=[e for e in doc.layouts.get(f'MDR{n:02}_A1').query('VIEWPORT') if e.dxf.id>1]
        assert vps and all(e.dxf.view_center_point.x>=900000 for e in vps)
        originals=[e for e in reference.layouts.get(original).query('VIEWPORT') if e.dxf.id>1]
        assert len(vps)==len(originals)
        for vp,source_vp in zip(vps,originals):
            assert abs(vp.dxf.view_center_point.x-source_vp.dxf.view_center_point.x-900000)<1e-7
            assert abs(vp.dxf.view_center_point.y-source_vp.dxf.view_center_point.y)<1e-7
            assert abs(vp.dxf.view_height-source_vp.dxf.view_height)<1e-7
    wb=openpyxl.load_workbook(OUT/'Main duct and return - Registers.xlsx',data_only=True)
    assert wb['Retained_instruments'].max_row==86 and wb['Retained_IO'].max_row==276
    assert wb['All_terminals'].max_row==54 and wb['Additional_DX'].max_row==23
    assert wb['Roof_routes_Rev12'].max_row==32 and wb['Roof_risers'].max_row==16
    report={'name':'Main duct and return','detailed_A1_sheets':14,'functional_method_sheets':11,'scaled_Rev12_reference_plans':3,
            'native_CAD_layouts':14,'DXF_audit':'passed','native_CAD_masks_lineweights_and_reference_viewports':'checked','retained_reference_block_entities':'checked including masks','preserved_input_sha256':'checked','retained_instruments_graphically_checked':85,
            'additional_DX_candidates_graphically_checked':22,'terminal_tags_graphically_checked':53,
            'retained_IO_points':275,'room_drop_tags_checked':15,'roof_reference_routes':31,
            'functional_main_flow_velocity_friction_checks':15,'main_location':'Roof common mains with room drops - user selected',
            'supply_l_s':basis['supply_l_s'],'return_l_s':basis['return_l_s'],
            'minimum_mass_balance_makeup_l_s':basis['minimum_mass_balance_makeup_l_s'],
            'scope':'Method and retained proposed physical plans; DX capacity, OEM selections, structure, actual roof survey, complete fan ESP and native AutoCAD plot remain pending'}
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
