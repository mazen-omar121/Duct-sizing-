"""Independent delivered roof graph, 3D-clearance and pressure-arithmetic checks."""
import csv,json,math
import fitz
from collections import defaultdict
from itertools import combinations
from shapely.geometry import LineString,box,Polygon
from shapely.ops import unary_union,transform

def validate(out,doc,wb):
    s=out/'cad-package/schedules'
    def rows(n):
        with (s/n).open() as f:return list(csv.DictReader(f))
    roof=rows('Roof_routes_Rev12.csv');risers=rows('Roof_risers.csv');paths=rows('Pressure_paths_Rev12.csv')
    assert len(roof)==31 and len(paths)==52
    residual=defaultdict(float);polys={};friction={};kinetic={};length={}
    for r in roof+rows('Duct_sections.csv'):
        q=float(r['flow_l_s']);w=float(r['width_mm'])/1000;h=float(r.get('height_mm') or 0)/1000;d=float(r.get('diameter_mm') or 0)/1000
        area=math.pi*d*d/4 if d else w*h;v=q/1000/area;dh=d if d else 2*w*h/(w+h)
        re=1.2*v*dh/1.81e-5;ff=.02
        for _ in range(30):ff=1/(-2*math.log10(.00009/(3.7*dh)+2.51/(re*math.sqrt(ff))))**2
        fr=ff/dh*.6*v*v;pp=json.loads(r['points_mm']);ll=sum(math.dist(a,b) for a,b in zip(pp,pp[1:]))/1000
        assert abs(v-float(r['velocity_m_s']))<.000021
        assert abs(fr-float(r['friction_pa_m']))<.000021
        friction[r['tag']]=fr;kinetic[r['tag']]=.6*v*v;length[r['tag']]=ll
        if r in roof:
            assert abs(ll-float(r['length_m']))<1e-6
            a,b=map(tuple,pp);residual[(r['air_type'],a)]+=q;residual[(r['air_type'],b)]-=q
            if float(r['taper_length_mm']):
                a,b=pp;ux,uy=(b[0]-a[0])/(ll*1000),(b[1]-a[1])/(ll*1000);nx,ny=-uy,ux
                developed=float(r['taper_length_mm']);c=[a[0]+ux*developed,a[1]+uy*developed]
                upstream=float(r['inlet_width_mm']);downstream=w*1000
                assert developed>=max(abs(upstream-downstream),abs(float(r['inlet_height_mm'])-h*1000))/(2*math.tan(math.radians(15)))
                def side(p,t):return (p[0]+nx*t,p[1]+ny*t)
                polys[r['tag']]=Polygon([side(a,upstream/2),side(c,downstream/2),side(b,downstream/2),side(b,-downstream/2),side(c,-downstream/2),side(a,-upstream/2)])
            else:polys[r['tag']]=LineString(pp).buffer(w*1000/2,cap_style=2,join_style=2)
    # Register every sink by actual shaft location, with independent node residuals.
    sinks={}
    for r in risers:
        key=(r['air_type'],(float(r['x_mm']),float(r['y_mm'])));sinks[key]=float(r['flow_l_s'])
        assert abs(residual[key]+sinks[key])<1e-6,(r['tag'],'roof duty discontinuity')
        q,w,h=map(float,[r['flow_l_s'],r['width_mm'],r['height_mm']]);area=w*h/1e6;v=q/1000/area;dh=2*w*h/(w+h)/1000
        re=1.2*v*dh/1.81e-5;ff=.02
        for _ in range(30):ff=1/(-2*math.log10(.00009/(3.7*dh)+2.51/(re*math.sqrt(ff))))**2
        friction[r['tag']]=ff/dh*.6*v*v;kinetic[r['tag']]=.6*v*v;length[r['tag']]=float(r['vertical_length_m'])
        assert length[r['tag']]==(int(r['roof_bod_mm_affl'])-3400)/1000
    roots={('SA',(2300,19000)):3697.8,('RA',(2700,17000)):3006.680337621642}
    for key,value in residual.items():
        expected=roots.get(key,-sinks.get(key,0));assert abs(value-expected)<1e-5,(key,value,expected)
    crosses=[]
    for a,b in combinations(roof,2):
        aa,bb=polys[a['tag']].buffer(75),polys[b['tag']].buffer(75)
        if a['air_type']==b['air_type']:
            pp,qq=json.loads(a['points_mm']),json.loads(b['points_mm']);shared=set(map(tuple,pp))&set(map(tuple,qq))
            if not shared:assert aa.intersection(bb).area<1,(a['tag'],b['tag'],'unconnected roof envelopes')
        elif aa.intersection(bb).area>1:
            lower,upper=(a,b) if a['air_type']=='SA' else (b,a)
            gap=int(upper['proposed_bod_mm_affl'])-int(lower['proposed_bod_mm_affl'])-float(lower['height_mm'])-150
            assert gap>=150;crosses.append((lower['tag'],upper['tag'],gap))
    registered=rows('Roof_crossings_Rev12.csv')
    assert {(r['lower'],r['upper'],float(r['clear_between_insulation_mm'])) for r in registered}==set(crosses)
    for r in risers:
        if r['air_type']!='RA':continue
        x,y,w,h=map(float,[r['x_mm'],r['y_mm'],r['width_mm'],r['height_mm']])
        shaft=box(x-w/2-75,y-h/2-75,x+w/2+75,y+h/2+75)
        for a in roof:
            if a['air_type']=='SA':assert shaft.intersection(polys[a['tag']].buffer(75)).area<1,(r['tag'],a['tag'])
    # Confirm roof exteriors exist in the delivered native DXF, not just source data.
    block=doc.blocks.get('PLAN_ROOF_PROPOSAL_D023');delivered={}
    for air in ['SA','RA']:
        lines=[]
        for e in block:
            if e.dxf.layer!='M-'+air+'-DUCT':continue
            if e.dxftype()=='LINE':lines.append(LineString([(e.dxf.start.x,e.dxf.start.y),(e.dxf.end.x,e.dxf.end.y)]))
        actual=unary_union(lines);expected=unary_union([polys[r['tag']] for r in roof if r['air_type']==air]).boundary
        assert expected.difference(actual.buffer(.2)).length<.2,(air,'roof exterior absent')
        delivered[air]=round(expected.length/1000,3)
    k=defaultdict(float)
    for r in rows('Fitting_design_Rev12.csv'):k[r['section']]+=float(r['quantity'])*float(r['assumed_K_each'])
    for r in paths:
        tags=r['roof_and_indoor_path'].split(' / ');straight=sum(length[t]*friction[t] for t in tags);local=sum(k[t]*kinetic[t] for t in tags)
        assert abs(straight-float(r['straight_loss_pa']))<.0015
        assert abs(local-float(r['assumed_fitting_loss_pa']))<.0015
        allowances=sum(float(r[t]) for t in ['assumed_heater_loss_pa','assumed_common_external_loss_pa','assumed_terminal_loss_pa'])
        total=straight+local+allowances
        assert abs(total-float(r['estimated_path_loss_pa']))<.002
        assert float(r['sensitivity_low_pa'])<=total<=float(r['sensitivity_high_pa'])
    inst=rows('Instrument_installation_Rev12.csv');requirements=rows('Instruments.csv')
    assert len(inst)==85 and {r['tag'] for r in inst}=={r['tag'] for r in requirements}
    assert len(rows('Terminal_performance_Rev12.csv'))==53
    for r in rows('Installation_envelopes_Rev12.csv'):
        assert float(r['lowest_reserved_mm_affl'])>=3300 and float(r['highest_reserved_mm_affl'])<=4000
    support=rows('Roof_supports_Rev12.csv')
    for route in roof:
        stations=[r for r in support if r['route']==route['tag']];pp=[(float(r['x_mm']),float(r['y_mm'])) for r in stations]
        assert max(math.dist(a,b) for a,b in zip(pp,pp[1:]))<=1501
    for title,n in [('Pressure_paths_Rev12',52),('Roof_routes_Rev12',31),('Instrument_install_Rev12',85),('Terminal_performance_Rev12',53)]:assert wb[title].max_row==n+1
    with fitz.open(out/'Administration_Detailed_HVAC_Duct_Flow_Diagram.pdf') as pdf:
        assert all(r['tag'] in pdf[22].get_text() for r in risers),'Roof plan has a clipped or missing drop label'
        assert '+5.550' in pdf[23].get_text() and '200 BETWEEN INSULATION AT RCX-03' in pdf[23].get_text()
        assert all(str(int(float(r['taper_length_mm']))) in pdf[24].get_text() for r in roof if float(r['taper_length_mm']))
    return {'roof_route_segments':31,'registered_drops':15,'roof_balanced_nodes':len(residual),'roof_plan_overlaps_with_vertical_separation':len(crosses),
            'minimum_roof_insulation_crossing_gap_mm':min(g for _,_,g in crosses),'return_risers_through_supply_routes':0,
            'delivered_roof_DXF_exterior_m':delivered,'pressure_path_arithmetic_checks':52,'instrument_installation_specs':85,
            'terminal_performance_screens':53,'support_reservations':len(support),
            'scope':'Proposed roof geometry / levels and explicit assumed loss model only. OEM selection, structural / roof survey and native AutoCAD plotting remain pending.'}
