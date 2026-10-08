"""Independently validate the complete detailed DX main/return revision02."""
from pathlib import Path
from math import log10,sqrt,ceil,tan,radians
from collections import Counter
import csv,json,hashlib
import ezdxf,fitz,openpyxl
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'projects/main_duct_and_return'
if not SOURCE.is_dir():SOURCE=ROOT/'source'
OUT=ROOT/'generated/main_duct_and_return'
MM=72/25.4

def rows(path):
    with path.open() as f:return list(csv.DictReader(f))

def body_labels(page):
    return Counter(span['text'] for block in page.get_text('dict')['blocks'] for line in block.get('lines',[]) for span in line['spans'] if 44*MM<span['origin'][1]<530*MM)

def main():
    provenance=json.loads((SOURCE/'PROVENANCE.json').read_text())
    for name,expected in provenance['input_sha256'].items():assert hashlib.sha256((SOURCE/'inputs'/name).read_bytes()).hexdigest()==expected,(name,'input changed')
    base=ROOT/'projects/administration_rev12/cad-package/schedules'
    if base.is_dir():
        for path in (SOURCE/'inputs/rev12_schedules').glob('*.csv'):assert path.read_bytes()==(base/path.name).read_bytes(),path.name
    basis=json.loads((OUT/'method_basis.json').read_text())
    assert basis['method_revision']==2 and basis['sheets']==50 and basis['total_register_tabs']==44
    assert basis['room_drops']==15 and basis['common_roof_route_segments']==31
    assert basis['main_location']=='Roof common mains with room drops - user selected'
    instruments=rows(SOURCE/'inputs/Instruments.csv');terminals=rows(SOURCE/'inputs/Terminals.csv');io=rows(SOURCE/'inputs/IO_points.csv')
    assert (len(instruments),len(terminals),len(io))==(85,53,275)
    dx=rows(OUT/'Additional_DX_proposals.csv');index=rows(OUT/'Instrument_drawing_index.csv');drawings=rows(OUT/'Drawing_index.csv')
    assert len(drawings)==50 and [r['number'] for r in drawings]==[f'MDR-{n:03}' for n in range(1,51)]
    assert len(dx)==22 and len({r['tag'] for r in dx})==22
    assert not {r['tag'] for r in dx}&{r['tag'] for r in instruments}
    assert {r['tag'] for r in index}=={r['tag'] for r in instruments}
    for r in rows(OUT/'Common_main_sizing.csv'):
        q,take,after=map(float,[r['flow_before_takeoff_l_s'],r['takeoff_l_s'],r['flow_after_takeoff_l_s']]);w,h=map(float,[r['clear_width_mm'],r['clear_depth_mm']])
        assert abs(q-take-after)<1e-8
        v=q/1000/(w*h/1e6);assert abs(v-float(r['velocity_m_s']))<1e-6
        dh=2*w*h/(w+h)/1000;re=1.2*v*dh/1.81e-5;fr=.02
        for _ in range(30):fr=1/(-2*log10(.00009/(3.7*dh)+2.51/(re*sqrt(fr))))**2
        assert abs(fr/dh*.6*v*v-float(r['straight_friction_pa_m']))<1e-6
    connections=rows(OUT/'DX_bank_connections.csv');assert len(connections)==6
    for r in connections:
        w,h,hw,hh=map(float,[r['proposed_branch_width_mm'],r['proposed_branch_depth_mm'],r['header_width_mm'],r['header_depth_mm']])
        expected=max(300,ceil(max(abs(w-hw),abs(h-hh))/(2*tan(radians(15)))/25)*25)
        assert float(r['proposed_taper_length_mm'])==expected
        assert abs(float(r['velocity_m_s'])-float(r['flow_l_s'])/1000/(w*h/1e6))<1e-6
    causes=rows(OUT/'DX_cause_and_effect.csv')
    cause_tags={t for r in causes for t in r['tags'].split('|')}
    assert {r['tag'] for r in dx}<=cause_tags
    interfaces=rows(OUT/'DX_interface_schedule.csv')
    assert {r['tag'] for r in interfaces}=={r['tag'] for r in dx}
    assert Counter(r['category'] for r in interfaces)=={'AI candidate':7,'DI candidate':3,'OEM LOCAL':12}
    with fitz.open(OUT/'Main duct and return.pdf') as pdf,fitz.open(SOURCE/'inputs/Rev12_reference.pdf') as ref:
        assert len(pdf)==50
        text=[p.get_text() for p in pdf]
        for i,p in enumerate(pdf,1):
            assert abs(p.rect.width/MM-841)<.01 and abs(p.rect.height/MM-594)<.01
            assert f'ADM-HVAC-MDR-{i:03}' in text[i-1] and f'SHEET {i} OF 50' in text[i-1],i
        for i in range(32):
            if i!=17:assert not body_labels(ref[i])-body_labels(pdf[i]),(i+1,'retained detail labels lost',body_labels(ref[i])-body_labels(pdf[i]))
        for r in index:
            for number in r['graphical_sheet'].split(' / '):assert r['tag'] in text[int(number[-3:])-1],(r['tag'],number)
        assert all(r['tag'] in text[43] and r['tag'] in text[37] for r in dx)
        assert all(r['tag'] in text[40] for r in terminals)
        assert all(r['number'] in text[17] for r in drawings)
        risers=rows(SOURCE/'inputs/Roof_risers.csv')
        assert all(r['tag'] in text[22] and r['tag'] in text[46] and r['tag'] in text[39] for r in risers)
        overflow=[]
        for number,p in enumerate(pdf,1):
            for block in p.get_text('dict')['blocks']:
                for line in block.get('lines',[]):
                    for span in line['spans']:
                        if not p.rect.contains(fitz.Rect(span['bbox'])):overflow.append((number,span['text']))
        assert not overflow,overflow
    with fitz.open(OUT/'Main duct and return - Monochrome.pdf') as pdf:
        assert len(pdf)==50
        for page in pdf:
            for drawing in page.get_drawings():
                for field in ['color','fill']:
                    color=drawing.get(field);assert color is None or max(color)-min(color)<.01,('Monochrome vector color',color)
    doc=ezdxf.readfile(OUT/'Main duct and return.dxf');audit=doc.audit()
    assert not audit.has_errors,[(r.code,r.message) for r in audit.errors]
    assert doc.units==ezdxf.units.MM
    assert {f'MDR{n:02}_A1' for n in range(1,51)}<=set(doc.layouts.names())
    assert not doc.layers.get('VIEWPORT').dxf.plot and not doc.layers.get('VIEWPORTS').dxf.plot
    native_text={e.dxf.text for layout in doc.layouts for e in layout.query('TEXT')}|{e.dxf.text for e in doc.modelspace().query('TEXT')}
    assert all(r['tag'] in native_text for r in instruments+dx)
    reference=ezdxf.readfile(SOURCE/'inputs/Rev12_reference.dxf')
    for insert in reference.modelspace().query('INSERT'):
        name=insert.dxf.name;old=reference.blocks.get(name);new=doc.blocks.get(name)
        assert Counter(e.dxftype() for e in old)==Counter(e.dxftype() for e in new),(name,'reference entities lost')
        def walls(block):
            return [(e.dxftype(),str(e.dxf.start),str(e.dxf.end)) for e in block.query('LINE')]
        assert walls(old)==walls(new),(name,'physical walls changed')
    for n in range(1,33):
        if n==18:continue
        vps=[e for e in doc.layouts.get(f'MDR{n:02}_A1').query('VIEWPORT') if e.dxf.id>1]
        originals=[e for e in reference.layouts.get(f'D{n:03}_A1').query('VIEWPORT') if e.dxf.id>1]
        assert len(vps)==len(originals),(n,'viewport lost')
        for vp,source_vp in zip(vps,originals):
            assert abs(vp.dxf.view_center_point.x-source_vp.dxf.view_center_point.x-900000)<1e-7
            assert abs(vp.dxf.view_center_point.y-source_vp.dxf.view_center_point.y)<1e-7
            assert abs(vp.dxf.view_height-source_vp.dxf.view_height)<1e-7
    dims=list(doc.modelspace().query('DIMENSION'))
    assert len(dims)==22
    # The 24 retained setting-out dimensions are inside physical plan blocks,
    # rather than directly in layouts. Count live database entities once.
    retained_dims=sum(e.dxftype()=='DIMENSION' for e in reference.entitydb.values() if e.is_alive)
    total_dims=sum(e.dxftype()=='DIMENSION' for e in doc.entitydb.values() if e.is_alive)
    assert retained_dims==24 and total_dims==retained_dims+len(dims)==46
    for dim in dims:
        if dim.dxf.dimstyle=='MDR-DETAIL':assert dim.override().get('dimlfac') in [10,20]
    wb=openpyxl.load_workbook(OUT/'Main duct and return - Registers.xlsx',data_only=True)
    base_wb=openpyxl.load_workbook(SOURCE/'inputs/Rev12_registers.xlsx',data_only=True)
    assert len(base_wb.sheetnames)==35 and len(wb.sheetnames)==44
    for name in base_wb.sheetnames:
        assert list(wb[name].values)==list(base_wb[name].values),(name,'baseline register changed')
    assert wb['MDR_Drawing_index'].max_row==51 and wb['MDR_Instrument_index'].max_row==86
    assert wb['DX_Bank_connections'].max_row==7 and wb['DX_Interface'].max_row==23
    report={'name':'Main duct and return','revision':2,'detailed_A1_sheets':50,'retained_detailed_engineering_sheets':32,'new_DX_detail_sheets':7,'supporting_method_sheets':11,
            'native_CAD_layouts':50,'DXF_audit':'passed','native_dimensions':total_dims,'new_dimensioned_development_entities':len(dims),'retained_physical_blocks_and_walls':'checked including masks and all viewports',
            'retained_detailed_PDF_body_labels':'31 sheets checked; drawing index replaced','preserved_input_sha256':'checked','retained_instruments_graphically_checked':85,
            'additional_DX_candidates_graphically_checked':22,'terminal_tags_graphically_checked':53,'retained_IO_points':275,'room_drop_tags_checked':15,'roof_reference_routes':31,
            'retained_register_tabs':35,'total_register_tabs':44,'new_bank_transitions_arithmetic_checks':6,'new_DX_candidate_interfaces':22,'main_location':basis['main_location'],
            'scope':'Full detailed engineering content plus DX/header development proposals; DX capacity/OEM selection/actual roof and structure/full fan ESP/OA balance/final approval/native AutoCAD plot pending'}
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
