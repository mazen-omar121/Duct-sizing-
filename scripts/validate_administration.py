"""Check delivered Rev11 CAD/PDF/registers, traceable revisions and conserved duties."""
import csv
import json
import math
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import ezdxf
import fitz
import openpyxl
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union, transform

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'generated' / 'administration'
SOURCE = ROOT / 'projects' / 'administration_rev11' / 'cad-package'
BASELINE = ROOT / 'projects' / 'administration_rev10' / 'cad-package' / 'schedules'


def records(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def line_clashes(rows):
    hits=[]
    for a,b in combinations(rows,2):
        if a['air_type']!=b['air_type']:continue
        ap,bp=json.loads(a['points_mm']),json.loads(b['points_mm'])
        overlap=LineString(ap).intersection(LineString(bp))
        if overlap.length>.1:
            hits.append((a['tag'],b['tag'],'retraced',round(overlap.length,2)))
        elif not overlap.is_empty:
            parts=[overlap] if overlap.geom_type=='Point' else list(getattr(overlap,'geoms',[]))
            endpoints=[Point(p) for p in [ap[0],ap[-1],bp[0],bp[-1]]]
            for p in parts:
                if p.geom_type=='Point' and min(p.distance(q) for q in endpoints)>.1:
                    hits.append((a['tag'],b['tag'],'unconnected crossing'))
    return hits


def main():
    schedule=OUT/'cad-package/schedules'
    sections=records(schedule/'Duct_sections.csv')
    assert sections==records(SOURCE/'schedules/Duct_sections.csv') and len(sections)==116
    terminals=records(schedule/'Terminals.csv')
    old_terms={r['tag']:r for r in records(BASELINE/'Terminals.csv')}
    moves=records(schedule/'Rev11_terminal_changes.csv')
    move_by_tag={r['tag']:r for r in moves}
    assert len(terminals)==53 and len(moves)==13
    observed_moves=set()
    for r in terminals:
        old=old_terms[r['tag']]
        assert {k:v for k,v in r.items() if k not in ['x_mm','y_mm']}=={k:v for k,v in old.items() if k not in ['x_mm','y_mm']}, ('Changed terminal duty / neck / face',r['tag'])
        if (r['x_mm'],r['y_mm'])!=(old['x_mm'],old['y_mm']):
            m=move_by_tag[r['tag']];observed_moves.add(r['tag'])
            assert tuple(float(m[k]) for k in ['old_x_mm','old_y_mm','new_x_mm','new_y_mm'])==tuple(float(x) for x in [old['x_mm'],old['y_mm'],r['x_mm'],r['y_mm']])
    assert observed_moves==set(move_by_tag)
    for name in ['Instruments.csv','IO_points.csv']:
        assert records(schedule/name)==records(BASELINE/name), ('Changed requirements',name)
    instruments=records(schedule/'Instruments.csv')
    index=records(schedule/'Instrument_drawing_index.csv')
    assert len(index)==len(instruments)==85 and {r['tag'] for r in index}=={r['tag'] for r in instruments}
    old_sections={r['tag']:r for r in records(BASELINE/'Duct_sections.csv')}
    resized={r['tag']:(r['previous_size_mm'],r['revised_size_mm']) for r in records(schedule/'Rev11_size_changes.csv')}
    actual_sizes={r['tag']:(old_sections[r['tag']]['width_mm']+'x'+old_sections[r['tag']]['height_mm'],r['width_mm']+'x'+r['height_mm']) for r in sections if r['tag'] in old_sections and (r['width_mm'],r['height_mm'])!=(old_sections[r['tag']]['width_mm'],old_sections[r['tag']]['height_mm'])}
    assert resized==actual_sizes
    assert not line_clashes(sections),line_clashes(sections)
    # This check rejects the bad legacy collection/runout geometry that triggered
    # the user's complaint. It is not a test that merely mirrors the new output.
    legacy_clashes=line_clashes(records(ROOT/'projects/administration_rev09/cad-package/schedules/Duct_sections.csv'))
    assert legacy_clashes,'Legacy regression no longer exercises the routing failure'
    nodes=defaultdict(list)
    for r in sections:
        pp=json.loads(r['points_mm']);q=float(r['flow_l_s'])
        for point,sign in [(pp[0],-1),(pp[-1],1)]:nodes[(r['air_type'],tuple(point))].append(q*sign)
        length=sum(math.dist(a,b) for a,b in zip(pp,pp[1:]))/1000
        assert abs(length-float(r['horizontal_length_m']))<.00011,(r['tag'],'length')
        w=float(r['width_mm'])/1000;h=float(r['height_mm'])/1000 if r['height_mm'] else None
        area=w*h if h else math.pi*w*w/4;v=q/1000/area;dh=2*w*h/(w+h) if h else w
        assert abs(v-float(r['velocity_m_s']))<.00002,(r['tag'],'velocity')
        re=1.2*v*dh/1.81e-5;ff=.02
        for _ in range(20):ff=1/(-2*math.log10(.00009/(3.7*dh)+2.51/(re*math.sqrt(ff))))**2
        friction=ff/dh*1.2*v*v/2
        assert abs(friction-float(r['friction_pa_m']))<.00002,(r['tag'],'straight friction')
    balanced=[sum(values) for values in nodes.values() if len(values)>1]
    assert max(map(abs,balanced))<.0001
    sys.path.insert(0,str(SOURCE/'src'))
    from duct_geometry import Network
    basis=json.loads((SOURCE/'inputs/Coordination_basis.json').read_text())
    network=Network(sections,19500,basis);geometry=network.validate()
    assert geometry['indoor_room_trees']=={'SA':9,'RA':6,'EA':2}
    assert not geometry['insulated_separate_service_clashes']
    assert not geometry['independent_service_crossings']
    crossing=records(schedule/'Crossing_register.csv');assert crossing==[]
    # Independently recompute full section envelopes and insulation separation.
    t=basis['external_insulation_mm'];bod=basis['proposed_indoor_bod_mm_affl']
    headroom=records(schedule/'Headroom_register.csv');head={r['section']:r for r in headroom}
    assert len(headroom)==len(sections)==116
    assert basis['finished_ceiling_mm_affl']==3300 and basis['structural_underside_mm_affl']==4000
    assert basis['installed_duct_bod_mm_affl'] is None and bod==3400
    by={r['tag']:r for r in sections}
    for r in sections:
        depth=float(r['height_mm'] or r['diameter_mm']);hr=head[r['tag']]
        assert depth<=400 and int(r['proposed_bod_mm_affl'])==bod
        assert bod-t-3300==float(hr['ceiling_clearance_mm'])==50
        assert 4000-(bod+depth+t)==float(hr['slab_clearance_mm'])>=150
        assert float(hr['lowest_insulated_mm_affl'])==3350
        assert float(hr['highest_insulated_mm_affl'])==bod+depth+t
        assert float(hr['bare_depth_mm'])==depth
    for a,b in combinations(network.envelopes,2):
        assert network.envelopes[a].buffer(t).intersection(network.envelopes[b].buffer(t)).area<1
    # A terminal face must not mask any passing duct of a different service or room.
    terminal_main_clashes=[]
    for term in terminals:
        x,y,w,h=map(float,[term['x_mm'],term['y_mm'],term['face_w_mm'],term['face_h_mm']])
        face=box(x-w/2,19500-y-h/2,x+w/2,19500-y+h/2)
        for r in sections:
            if r['air_type']==term['air_type'] and r['room']==term['room']:continue
            area=face.intersection(network.polygons[r['tag']]).area
            if area>1:terminal_main_clashes.append((term['tag'],r['tag'],area))
    assert not terminal_main_clashes,terminal_main_clashes
    risers=records(schedule/'Roof_risers.csv');roof=records(schedule/'Roof_main_basis.csv')
    assert len(risers)==len(roof)==15
    branches={r['tag']:r for r in sections if r['role']=='Branch'}
    assert {r['branch'] for r in risers}==set(branches)
    ends=set()
    for r in risers:
        branch=branches[r['branch']];pp=json.loads(branch['points_mm'])
        x,y=pp[0 if r['air_type']=='SA' else -1]
        assert (float(r['x_mm']),float(r['y_mm']))==(x,y)
        assert abs(float(r['flow_l_s'])-float(branch['flow_l_s']))<.00001
        assert (r['width_mm'],r['height_mm'])==(branch['width_mm'],branch['height_mm'])
        assert r['roof_bod_mm_affl']==r['vertical_length_m']=='TBC'
        ends.add((r['air_type'],(x,19500-y)))
    # No concealed free branch end: every singleton graph node must be a
    # scheduled terminal, roof drop or dedicated extract outlet.
    for r in terminals:
        if r['tag']=='EG-01-01':continue  # CAG duty is TBC; separately drawn dedicated extract marker.
        ends.add((r['air_type'],(float(r['x_mm']),19500-float(r['y_mm']))))
    for r in sections:
        if r['role']=='Extract branch':
            x,y=json.loads(r['points_mm'])[-1];ends.add((r['air_type'],(x,19500-y)))
    actual_ends={(air,(pt[0],19500-pt[1])) for (air,pt),v in nodes.items() if len(v)==1}
    assert actual_ends==ends,('Unallocated free duct ends',actual_ends-ends,ends-actual_ends)
    for air in ['SA','RA']:
        chain=[r for r in roof if r['air_type']==air]
        room_order=['02','05','04','08','06','09','07','03','01'] if air=='SA' else ['02','05','04','08','06','07']
        expected=[sum(float(branches[air+'-B'+room]['flow_l_s']) for room in room_order[i:]) for i in range(len(room_order))]
        for r,q in zip(chain,expected):assert abs(float(r['flow_l_s'])-q)<.0001,(r['tag'],'Roof functional flow',q)
    devices=records(schedule/'Device_locations.csv')
    assert len(devices)==56 and len([r for r in devices if r['tag'].startswith('AD-')])==21
    roof_ad=next(r for r in devices if r['tag']=='AD-HCOM-01');assert roof_ad['x_mm']==roof_ad['y_mm']=='TBC'
    for r in devices:
        if r['room']=='COM' or r['tag'].startswith('AD-'):continue
        sec=by[r['service']+'-B'+r['room']];pp=json.loads(sec['points_mm'])
        total=sum(math.dist(a,b) for a,b in zip(pp,pp[1:]));xy=(float(r['x_mm']),float(r['y_mm']))
        along=LineString(pp).project(Point(xy))
        core={'VCD':64.8649,'RCD':72.24,'FSD':105.3,'EH':147.95}[r['tag'].split('-')[0]]/2
        clearance=max(200,float(sec['height_mm'])*.75)
        assert (along-core if sec['air_type']=='SA' else total-along-core)>=clearance-1,(r['tag'],'Riser elbow separation')
    detailed=ezdxf.readfile(OUT/'Administration_HVAC_Detailed_Layout.dxf')
    assert detailed.units==ezdxf.units.MM and not detailed.audit().has_errors
    assert len([n for n in detailed.layouts.names() if n.startswith('D') and n.endswith('_A1')])==22
    dimensions=[e for block in detailed.blocks for e in block.query('DIMENSION')]
    assert len(dimensions)==11
    assert sorted(round(e.get_measurement()) for e in dimensions)==sorted([1500,3300,3700,11500,20000,5600,3250,1850,5900,2900,19500])
    plan=detailed.blocks.get('PLAN_COORDINATION_D001')
    coverage={}
    for air in ['SA','RA','EA']:
        lines=[]
        for e in plan:
            if e.dxf.layer!='M-'+air+'-DUCT':continue
            if e.dxftype()=='LINE':lines.append(LineString([(e.dxf.start.x,e.dxf.start.y),(e.dxf.end.x,e.dxf.end.y)]))
            elif e.dxftype()=='LWPOLYLINE':
                pp=list(e.get_points('xy'))
                if e.closed:pp.append(pp[0])
                if len(pp)>1:lines.append(LineString(pp))
        actual=unary_union(lines);expected=transform(lambda x,y:(x,19500-y),network.envelopes[air].boundary)
        missing=expected.difference(actual.buffer(.2)).length
        assert missing<.2,(air,'Missing delivered DXF exterior',missing)
        coverage[air]=round(expected.length/1000,3)
    assert {r['tag'] for r in crossing}<={e.dxf.text for e in plan.query('TEXT')}
    cag=[e for e in plan.query('INSERT') if any(a.dxf.tag=='TAG' and a.dxf.text=='EG-01-01' for a in e.attribs)]
    assert len(cag)==1 and cag[0].dxf.name=='HVAC_EG'
    assert (cag[0].dxf.insert.x,cag[0].dxf.insert.y)==(18600,1500)
    ea_lines=[]
    for e in plan:
        if e.dxf.layer!='M-EA-DUCT':continue
        if e.dxftype()=='LINE':ea_lines.append(LineString([(e.dxf.start.x,e.dxf.start.y),(e.dxf.end.x,e.dxf.end.y)]))
        elif e.dxftype()=='LWPOLYLINE':
            pp=list(e.get_points('xy'))
            if e.closed:pp.append(pp[0])
            if len(pp)>1:ea_lines.append(LineString(pp))
    cag_expected=box(18600,1350,20800,1650).boundary
    assert cag_expected.difference(unary_union(ea_lines).buffer(.2)).length<.2
    inst_plan=detailed.blocks.get('PLAN_INSTRUMENTATION_D007')
    assert len([e for e in inst_plan.query('TEXT') if e.dxf.text=='3 AI TO HPCP-01 / D-015'])==9
    assert len([e for e in inst_plan.query('TEXT') if e.dxf.text=='(-) OUTDOOR REF.'])==9
    for letter in 'ABCDEF':assert 'PLAN_JUNCTION_'+letter+'_D019' in detailed.blocks
    schematic=ezdxf.readfile(OUT/'Administration_HVAC_Schematic.dxf')
    assert not schematic.audit().has_errors
    checked_refs=0
    with fitz.open(OUT/'Administration_Detailed_HVAC_Duct_Flow_Diagram.pdf') as pdf:
        assert len(pdf)==22
        texts=[p.get_text() for p in pdf]
        for p in pdf:assert abs(p.rect.width*25.4/72-841)<.01 and abs(p.rect.height*25.4/72-594)<.01
        for r in index:
            for ref in r['drawings'].split(' / '):
                number=int(ref);assert number!=16
                assert r['tag'] in texts[number-1],(r['tag'],ref)
                checked_refs+=1
        for r in crossing:
            assert r['tag'] in texts[0] and r['tag'] in texts[19],r['tag']
        assert '+4.000' in texts[19] and '+3.300' in texts[19] and '+3.400' in texts[19]
        assert all(r['tag'] in texts[0] and r['tag'] in texts[21] for r in risers)
        for i,txt in enumerate(texts,1):assert f'SHEET {i} OF 22' in txt and 'REVISION' in txt
        assert all(r['tag'] in texts[20] for r in moves)
        overflow=[]
        for number,page in enumerate(pdf,1):
            for block in page.get_text('dict')['blocks']:
                for line in block.get('lines',[]):
                    for span in line['spans']:
                        if not page.rect.contains(fitz.Rect(span['bbox'])):overflow.append((number,span['text']))
        assert not overflow,overflow
    for name,count in [('Administration_Detailed_HVAC_Duct_Flow_Diagram_Monochrome.pdf',22),('Administration_HVAC_Schematic.pdf',4)]:
        with fitz.open(OUT/name) as pdf:assert len(pdf)==count
    wb=openpyxl.load_workbook(OUT/'Administration_HVAC_Drawing_Registers_Rev11.xlsx',data_only=True)
    assert len(wb.sheetnames)==23 and wb['Instruments'].max_row==86
    assert wb['Instrument_drawing_index'].max_row==86 and wb['Sizing_check'].max_row==117
    assert wb['Crossing_register'].max_row==1 and wb['Rev11_terminal_changes'].max_row==14
    assert wb['Rev11_size_changes'].max_row==len(resized)+1
    for row in list(wb['Sizing_check'].values)[1:]:
        flow,w,h,d=row[3:7];area=math.pi*(d/1000)**2/4 if d else w*h/1e6
        assert abs(flow/1000/area-row[8])<1e-9
    report={'revision':11,'detailed_sheets':22,'schematic_sheets':4,'monochrome_sheets':22,
            'duct_sections':116,'terminal_duties':53,'documented_terminal_moves':13,'documented_size_changes':len(resized),
            'instrument_tags':85,'instrument_sheet_references_checked':checked_refs,'native_dimensions':11,
            'room_signal_trunks':9,'outdoor_reference_annotations':9,'DXF_audits':'passed','delivered_DXF_exteriors_m':coverage,
            'same_service_centerline_clashes':[],'same_service_polygon_clashes':[],'terminal_faces_over_passing_other_service_or_room_ducts':[],
            'legacy_centerline_regressions_rejected':len(legacy_clashes),'balanced_airflow_nodes':len(balanced),
            'instrument_and_IO_requirements':'unchanged from published Rev10','terminal_duties_neck_face_sizes':'unchanged from Rev10',
            'graph_terminal_connections':52,'CAG_extract_marker':'Dedicated schematic connection shown; airflow / final pickup elevation TBC',
            'workbook_sheets':23,'velocities_lengths_friction_recalculated':116,'separate_service_crossings':0,'insulated_separate_service_clashes':[],'roof_riser_proposals':15,'roof_functional_main_sections':15,'indoor_room_trees':geometry['indoor_room_trees'],
            'coordination_basis':basis,'minimum_ceiling_clearance_mm':50,'minimum_slab_clearance_mm':150,'maximum_indoor_bare_depth_mm':400,'native_AutoCAD_plot':'not run','DWG_export':'AutoCAD Save As from DXF',
            'engineering_holds':['Roof option selection; actual roof routing / structure / penetrations / loads / curbs / weather insulation / vertical development; OEM terminal plenums, flanges, actuators, supports and access within the proposed ceiling envelope',
                                 'pressure / outdoor-air balance','selected fitting K / fan ESP / OEM selections',
                                 'fire boundaries / I&C settings and final wiring']}
    (OUT/'independent_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
