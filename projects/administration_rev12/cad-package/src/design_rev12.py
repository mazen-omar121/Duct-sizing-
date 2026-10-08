"""Provisional engineering design, explicit assumptions and calculated schedules.

Roof coordinates are proposals on the supplied floor footprint, not a roof survey.
Loss coefficients and equipment allowances below are sensitivity assumptions,
not selected ASHRAE/SMACNA fittings or manufacturer performance.
"""
import csv, json, math
from pathlib import Path
from collections import defaultdict
from itertools import combinations
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union
from shapely.geometry import Polygon

BASE=Path(__file__).resolve().parents[1]
S=BASE/'schedules'
def read(name):
    with (S/name).open() as f:return list(csv.DictReader(f))
def write(name, rows):
    with (S/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def hydraulic(q,w,h=0,d=0):
    area=math.pi*(d/1000)**2/4 if d else w*h/1e6
    v=q/1000/area;dh=d/1000 if d else 2*w*h/(w+h)/1000
    if not q:return area,v,0
    re=1.2*v*dh/1.81e-5;ff=.02
    for _ in range(30):ff=1/(-2*math.log10(.00009/(3.7*dh)+2.51/(re*math.sqrt(ff))))**2
    return area,v,ff/dh*1.2*v*v/2
def roof_polygon(r):
    a,b=json.loads(r['points_mm']);w=float(r['width_mm']);up=float(r['inlet_width_mm']);ll=float(r['taper_length_mm'])
    if not ll:return LineString([a,b]).buffer(w/2,cap_style=2,join_style=2)
    length=math.dist(a,b);ux,uy=(b[0]-a[0])/length,(b[1]-a[1])/length;nx,ny=-uy,ux
    c=[a[0]+ll*ux,a[1]+ll*uy]
    def side(p,d):return (p[0]+nx*d,p[1]+ny*d)
    return Polygon([side(a,up/2),side(c,w/2),side(b,w/2),side(b,-w/2),side(c,-w/2),side(a,-up/2)])
def generate():
    sections=read('Duct_sections.csv');risers=read('Roof_risers.csv')
    by={r['tag']:r for r in sections};rby={r['branch']:r for r in risers}
    basis={'revision':12,'source_plan_extent_mm':[20000,19500],
           'roof_surface_mm_affl':4200,'slab_thickness_assumption_mm':200,
           'roof_sa_bod_mm_affl':4800,'roof_ra_bod_mm_affl':5550,
           'outdoor_insulation_assumption_mm':75,'indoor_insulation_assumption_mm':50,
           'minimum_roof_crossing_clearance_mm':150,
           'PAU_reservation_each_mm':[1600,2500],'PAU_service_strip_width_mm':1000,
           'roof_support_spacing_max_proposal_mm':1500,
           'curb_upstand_proposal_mm':300,'curb_annular_allowance_each_side_mm':100,
           'elbow_centerline_radius_factor':1.0,'taper_included_angle_max_proposal_deg':30,
           'assumed_K_elbow':.5,'assumed_K_tee_branch':1.0,'assumed_K_tee_run':.2,
           'assumed_K_adapter':.25,'assumed_K_balancing_damper':2.0,
           'assumed_K_fire_damper':1.0,'assumed_terminal_loss_pa':30,
           'assumed_common_external_equipment_loss_pa':150,'fan_budget_margin_percent':20,
           'status':'COORDINATION PROPOSAL. All roof levels, slab thickness, footprints, insulation, K and device loss allowances require site / OEM confirmation. No selected fan or certified acoustic performance.'}
    (BASE/'inputs/Engineering_basis_Rev12.json').write_text(json.dumps(basis,indent=2)+'\n')
    roof=[]
    def edge(tag,air,a,b,q,w,h,role='Roof branch',room='COM'):
        area,v,fr=hydraulic(q,w,h);ll=math.dist(a,b)/1000
        roof.append(dict(tag=tag,air_type=air,role=role,room=room,points_mm=json.dumps([a,b]),
                         flow_l_s=q,width_mm=w,height_mm=h,length_m=round(ll,6),
                         velocity_m_s=round(v,6),friction_pa_m=round(fr,6),
                         proposed_bod_mm_affl=basis['roof_'+air.lower()+'_bod_mm_affl'],
                         status='Proposed route / level; roof survey and structural approval pending'))
    # Two split columns conserve actual room duties at the vertical takeoffs.
    sa_groups=[(3600,['02','04']),(8200,['08']),(12500,['05','06']),
               (13400,['09']),(15500,['07']),(17000,['03']),(18100,['01'])]
    ra_groups=[(4800,['04']),(6000,['02']),(9400,['08']),(11300,['06']),(13000,['07']),(19500,['05'])]
    for air,groups,root,y,w,h in [('SA',sa_groups,2300,19000,600,1300),('RA',ra_groups,2700,17000,700,900)]:
        previous=root
        for n,(x,rooms) in enumerate(groups,1):
            q=sum(float(by[air+'-B'+rr]['flow_l_s']) for _,rs in groups[n-1:] for rr in rs)
            edge(f'R-{air}-M{n:02}',air,[previous,y],[x,y],q,w,h,'Roof main');previous=x
            if len(rooms)==2:
                first,second=rooms;rr=rby[air+'-B'+first];yy=float(rr['y_mm'])
                q=sum(float(by[air+'-B'+r]['flow_l_s']) for r in rooms)
                edge(f'R-{air}-{first}-{second}',air,[x,y],[x,yy],q,700,450 if first=='02' else 400,room=first+' / '+second)
                rr2=rby[air+'-B'+second];target=[float(rr2['x_mm']),float(rr2['y_mm'])]
                mid=[x,target[1]];b=by[air+'-B'+second]
                edge(f'R-{air}-{second}A',air,[x,yy],mid,float(b['flow_l_s']),float(b['width_mm']),float(b['height_mm']),room=second)
                if mid!=target:edge(f'R-{air}-{second}B',air,mid,target,float(b['flow_l_s']),float(b['width_mm']),float(b['height_mm']),room=second)
            else:
                room=rooms[0];rr=rby[air+'-B'+room];target=[float(rr['x_mm']),float(rr['y_mm'])]
                b=by[air+'-B'+room];mid=[x,target[1]]
                edge(f'R-{air}-{room}A',air,[x,y],mid,float(b['flow_l_s']),float(b['width_mm']),float(b['height_mm']),room=room)
                if mid!=target:edge(f'R-{air}-{room}B',air,mid,target,float(b['flow_l_s']),float(b['width_mm']),float(b['height_mm']),room=room)
    for r in roof:
        r['inlet_width_mm']=r['width_mm'];r['inlet_height_mm']=r['height_mm'];r['taper_length_mm']=0
        if r['tag'] in ['R-SA-04A','R-SA-06A']:
            r['inlet_width_mm']=700;r['inlet_height_mm']=450 if r['tag']=='R-SA-04A' else 400
            delta=max(abs(700-float(r['width_mm'])),abs(r['inlet_height_mm']-float(r['height_mm'])))
            r['taper_length_mm']=math.ceil(max(300,delta/(2*math.tan(math.radians(15))))/25)*25
    write('Roof_routes_Rev12.csv',roof)
    # Measured rise between horizontal duct centerlines, not BOD difference.
    for r in risers:
        bod=basis['roof_'+r['air_type'].lower()+'_bod_mm_affl'];depth=float(r['height_mm'])
        r['roof_bod_mm_affl']=bod;r['vertical_length_m']=round((bod-3400)/1000,6)
        r['level_status']='PROPOSED: centerline rise with equal duct depth at both ends; roof thickness / beams / penetration and bend development unverified'
    write('Roof_risers.csv',risers)
    footprints={r['tag']:roof_polygon(r) for r in roof}
    crosses=[];conflicts=[]
    for a,b in combinations(roof,2):
        pa,pb=footprints[a['tag']],footprints[b['tag']]
        if a['air_type']==b['air_type']:
            pp,qq=json.loads(a['points_mm']),json.loads(b['points_mm'])
            shared=set(map(tuple,pp))&set(map(tuple,qq))
            inter=LineString(pp).intersection(LineString(qq))
            if inter.length>.1 or (not inter.is_empty and not shared):conflicts.append([a['tag'],b['tag'],'unconnected same-service centerline'])
            if not shared and pa.buffer(75).intersection(pb.buffer(75)).area>1:conflicts.append([a['tag'],b['tag'],'same-service insulation overlap'])
        elif pa.buffer(75).intersection(pb.buffer(75)).area>1:
            lower,upper=(a,b) if a['air_type']=='SA' else (b,a)
            clear=float(upper['proposed_bod_mm_affl'])-75-(float(lower['proposed_bod_mm_affl'])+float(lower['height_mm'])+75)
            inter=pa.intersection(pb);center=inter.centroid if not inter.is_empty else pa.buffer(75).intersection(pb.buffer(75)).centroid
            crosses.append(dict(tag=f'RCX-{len(crosses)+1:02}',lower=lower['tag'],upper=upper['tag'],x_mm=round(center.x),y_mm=round(center.y),
                                clear_between_insulation_mm=clear,status='Proposed separated levels; structural / support coordination pending'))
            if clear<150:conflicts.append([a['tag'],b['tag'],'insufficient vertical crossing clearance'])
    # Upper return risers must not pass through lower roof supply ducts.
    for r in risers:
        if r['air_type']!='RA':continue
        x,y,w,h=map(float,[r['x_mm'],r['y_mm'],r['width_mm'],r['height_mm']])
        shaft=box(x-w/2-75,y-h/2-75,x+w/2+75,y+h/2+75)
        for a in roof:
            if a['air_type']=='SA' and shaft.intersection(footprints[a['tag']].buffer(75)).area>1:
                conflicts.append([r['tag'],a['tag'],'return shaft through supply route'])
    assert not conflicts,conflicts
    write('Roof_crossings_Rev12.csv',crosses)
    support=[]
    for r in roof:
        a,b=json.loads(r['points_mm']);count=max(1,math.ceil(float(r['length_m'])*1000/1500))
        for i in range(count+1):
            t=i/count;x=a[0]+t*(b[0]-a[0]);y=a[1]+t*(b[1]-a[1])
            support.append(dict(tag=f'SUP-{r["tag"]}-{i+1:02}',route=r['tag'],x_mm=round(x),y_mm=round(y),
                                maximum_spacing_mm=1500,type='Proposed adjustable nonpenetrating frame; support at fitting subject to shop detail',
                                load_kg='TBC - duct gauge / insulation / frame / wind loads',status='No roof anchor / ballast / structural selection'))
    write('Roof_supports_Rev12.csv',support)
    curbs=[]
    for r in risers:
        w,h=map(float,[r['width_mm'],r['height_mm']])
        curbs.append(dict(tag='CURB-'+r['tag'],riser=r['tag'],x_mm=r['x_mm'],y_mm=r['y_mm'],
                          reserved_opening_x_mm=w+2*(75+100),reserved_opening_y_mm=h+2*(75+100),upstand_above_roof_mm=300,
                          detail='D-024 / D-030',status='Reserved opening only; structure, sleeve, waterproofing, firestop and anchor approval required'))
    write('Roof_curbs_Rev12.csv',curbs)
    # Catalogues are absent: every coefficient below is explicitly assumed.
    fittings=[];loss=defaultdict(float);geometry=[]
    all_sections={r['tag']:r for r in sections+roof}
    def fit(section,kind,k,w,h,d=0,qty=1,position=None):
        tag=f'F12-{len(fittings)+1:03}';radius=round(w);length=round(max(300,w))
        if position is None:
            if section in all_sections:position=json.loads(all_sections[section]['points_mm'])[0]
            else:
                rr=next(r for r in risers if r['tag']==section);position=[float(rr['x_mm']),float(rr['y_mm'])]
        fittings.append(dict(tag=tag,section=section,type=kind,quantity=qty,clear_w_mm=w,clear_h_or_d_mm=d or h,
                             node_x_mm=position[0],node_y_mm=position[1],
                             proposed_centerline_radius_mm=radius if 'elbow' in kind.lower() else '-',
                             proposed_development_mm=length if 'adapter' in kind.lower() or 'tee' in kind.lower() else '-',
                             assumed_K_each=k,K_basis='Rev12 transparent preliminary allowance; replace with selected geometry / catalogue coefficient',
                             fabrication_status='Proposed geometry; verify available straight length and OEM body dimensions'))
        loss[section]+=k*qty;return tag
    for r in sections+roof:
        w=float(r['width_mm']);h=float(r.get('height_mm') or 0);d=float(r.get('diameter_mm') or 0);pp=json.loads(r['points_mm'])
        for p in pp[1:-1]:fit(r['tag'],'90 degree elbow',.5,w,h,d,position=p)
        if r['role']=='Runout':fit(r['tag'],'Terminal adapter',.25,w,h,d,position=pp[-1])
        if r['role']=='Branch':
            fit(r['tag'],'Balancing damper allowance',2,w,h,d)
            fit(r['tag'],'Conditional fire damper allowance',1,w,h,d)
            if r['room'] in ['04','05','06','07','03'] and r['air_type']=='SA':
                # Dimensional envelope is assessed separately; loss 25 Pa is not a K.
                pass
    # Allocate junction coefficients once on the outgoing oriented tree edges.
    for rows in [sections,roof]:
        starts=defaultdict(list);ends=defaultdict(list)
        for r in rows:
            pp=json.loads(r['points_mm']);a,b=pp[0],pp[-1]
            if rows is sections and r['air_type'] in ['RA','EA']:a,b=b,a
            starts[(r['air_type'],tuple(a))].append(r);ends[(r['air_type'],tuple(b))].append(r)
        for key,outgoing in starts.items():
            incoming=ends[key]
            if not incoming:continue
            for r in outgoing:
                w,h,d=map(float,[r['width_mm'],r.get('height_mm') or 0,r.get('diameter_mm') or 0])
                parent=incoming[0];ap=json.loads(parent['points_mm']);bp=json.loads(r['points_mm'])
                if rows is sections and r['air_type'] in ['RA','EA']:ap.reverse();bp.reverse()
                va=[ap[-1][j]-ap[-2][j] for j in [0,1]];vb=[bp[1][j]-bp[0][j] for j in [0,1]]
                straight=sum(a*b for a,b in zip(va,vb))>0 and abs(va[0]*vb[1]-va[1]*vb[0])<.001
                tee=len(outgoing)>1 or abs(float(parent['flow_l_s'])-float(r['flow_l_s']))>.001
                if tee:fit(r['tag'],'Tee straight run allowance' if straight else 'Tee branch allowance',.2 if straight else 1,w,h,d,position=key[1])
                elif not straight:fit(r['tag'],'Joint / bend allowance',.5,w,h,d,position=key[1])
    for r in risers:
        fit(r['tag'],'Riser elbows (two)',.5,float(r['width_mm']),float(r['height_mm']),qty=2)
        fit(r['tag'],'Roof / riser adapter allowance',.25,float(r['width_mm']),float(r['height_mm']))
    write('Fitting_design_Rev12.csv',fittings)
    # Proposals for every extant adapter: slope-based development, not OEM length.
    for r in read('Transitions_and_takeoffs.csv'):
        row=dict(r);row['Rev12_detail']='D-025'
        row['Rev12_fabrication_hold']='Opening / radius follows connected model; develop shop fitting after selecting terminal plenum'
        geometry.append(row)
    write('Adapter_details_Rev12.csv',geometry)
    def path(rows,air,target):
        incoming={}
        for r in rows:
            if r['air_type']!=air:continue
            pp=json.loads(r['points_mm']);a,b=pp[0],pp[-1]
            if rows is sections and air in ['RA','EA']:a,b=b,a
            assert tuple(b) not in incoming,('Tree has multiple parents',r['tag'])
            incoming[tuple(b)]=(r,tuple(a))
        result=[];pt=tuple(target)
        while pt in incoming:
            r,pt=incoming[pt];result.append(r)
            assert len(result)<=len(rows),'Cycle'
        return list(reversed(result)),pt
    paths=[];lossrows=[]
    for term in read('Terminals.csv'):
        if term['flow_l_s']=='TBC':continue
        air=term['air_type'];xy=[float(term['x_mm']),float(term['y_mm'])]
        indoor,root=path(sections,air,xy)
        assert indoor,term['tag']
        extra=[];riser=None;rise=0
        if air in ['SA','RA']:
            rr=next(r for r in risers if (float(r['x_mm']),float(r['y_mm']))==root and r['air_type']==air)
            extra,roofroot=path(roof,air,root);riser=rr;rise=float(rr['vertical_length_m'])
        straight=local=0;trace=[]
        for r in extra+indoor:
            tag=r['tag'];trace.append(tag)
            ll=float(r.get('length_m',r.get('horizontal_length_m')));fr=float(r['friction_pa_m']);v=float(r['velocity_m_s'])
            straight+=ll*fr;local+=loss[tag]*.6*v*v
        if riser:
            tag=riser['tag'];trace.insert(len(extra),tag)
            _,v,fr=hydraulic(float(riser['flow_l_s']),float(riser['width_mm']),float(riser['height_mm']))
            straight+=rise*fr;local+=loss[tag]*.6*v*v
        heater=25 if air=='SA' and term['room'] in ['04','05','06','07','03'] else 0
        common=150 if air=='SA' else 0;terminal=30
        total=straight+local+heater+common+terminal
        paths.append(dict(terminal=term['tag'],air_type=air,room=term['room'],flow_l_s=term['flow_l_s'],
                          roof_and_indoor_path=' / '.join(trace),vertical_rise_m=rise,straight_loss_pa=round(straight,3),
                          assumed_fitting_loss_pa=round(local,3),assumed_heater_loss_pa=heater,
                          assumed_common_external_loss_pa=common,assumed_terminal_loss_pa=terminal,
                          estimated_path_loss_pa=round(total,3),sensitivity_low_pa=round(straight+.5*(local+heater+common+terminal),3),
                          sensitivity_high_pa=round(straight+1.5*(local+heater+common+terminal),3),
                          status='Preliminary allowance model; terminal / fitting / selected equipment losses and PAU connection paths pending'))
    write('Pressure_paths_Rev12.csv',paths)
    worst={air:max((r for r in paths if r['air_type']==air),key=lambda r:r['estimated_path_loss_pa']) for air in ['SA','RA','EA']}
    combined=worst['SA']['estimated_path_loss_pa']+worst['RA']['estimated_path_loss_pa']
    fans=[dict(system='PAU bank - combined external SA + RA path',duty_flow_each_l_s=1848.9,
               configuration='2 duty + 1 standby; all three individually rated for 50% total flow',
               estimated_external_loss_pa=round(combined,3),provisional_ESP_with_20_percent_margin_pa=math.ceil(combined*1.2/10)*10,
               low_sensitivity_pa=round(worst['SA']['sensitivity_low_pa']+worst['RA']['sensitivity_low_pa'],3),
               high_sensitivity_pa=round(worst['SA']['sensitivity_high_pa']+worst['RA']['sensitivity_high_pa'],3),
               internal_unit_losses='OEM to include filters at dirty condition / coils / internal dampers; do not add twice to external budget',
               selection_status='No fan selected; include PAU nozzle / common-plant routing / OA intake and dirty-filter interpretation before fan curve approval')]
    for room in ['03','09']:
        w=max((r for r in paths if r['air_type']=='EA' and r['room']==room),key=lambda r:r['estimated_path_loss_pa'])
        fans.append(dict(system='EF-'+room+' duty / standby',duty_flow_each_l_s=sum(float(r['flow_l_s']) for r in paths if r['air_type']=='EA' and r['room']==room),
                         configuration='One duty and one standby at full room extract',estimated_external_loss_pa=w['estimated_path_loss_pa'],
                         provisional_ESP_with_20_percent_margin_pa=math.ceil(w['estimated_path_loss_pa']*1.2/10)*10,
                         low_sensitivity_pa=w['sensitivity_low_pa'],high_sensitivity_pa=w['sensitivity_high_pa'],
                         internal_unit_losses='Outlet / louver / standby branch / discharge loss pending',selection_status='No fan selected; final discharge and curve verification pending'))
    write('Fan_budget_Rev12.csv',fans)
    data=json.loads((BASE/'inputs/Administration_design_basis.json').read_text());balances=[];sa=ra=ea=0
    for room in data['rooms']:
        rid=room['id'];qsa=float(room['sa']);qra=float(room['ra']);terms=[t for t in read('Terminals.csv') if t['air_type']=='EA' and t['room']==rid]
        qe=sum(float(t['flow_l_s']) for t in terms if t['flow_l_s']!='TBC');unknown=any(t['flow_l_s']=='TBC' for t in terms)
        sa+=qsa;ra+=qra;ea+=qe
        net=qsa-qra-qe
        balances.append(dict(room=rid,supply_l_s=qsa,return_l_s=qra,known_extract_l_s=qe,unresolved_extract=unknown,
                             residual_to_transfer_or_leakage_l_s=round(net,6),pressure_target_pa=50 if room['rn'] else 25,
                             target_verification='Not established; leakage / transfer openings and EA selection required',
                             engineering_action='Resolve positive-pressure requirement versus hygiene extract and transfer design' if rid in ['09','03','01'] else 'Balance RA then verify pressure under door / leakage conditions'))
    write('Air_balance_Rev12.csv',balances)
    performance=[]
    for t in read('Terminals.csv'):
        q=None if t['flow_l_s']=='TBC' else float(t['flow_l_s']);d=None if t['neck_dia_mm']=='TBC' else float(t['neck_dia_mm'])
        peers=[r for r in read('Terminals.csv') if r['room']==t['room'] and r['air_type']==t['air_type'] and r['tag']!=t['tag']]
        distance=min((math.dist((float(t['x_mm']),float(t['y_mm'])),(float(p['x_mm']),float(p['y_mm']))) for p in peers),default=None)
        performance.append(dict(tag=t['tag'],room=t['room'],air_type=t['air_type'],flow_l_s=t['flow_l_s'],neck_mm=t['neck_dia_mm'],
                                neck_velocity_m_s=round(q/1000/(math.pi*(d/1000)**2/4),3) if q is not None and d else 'TBC',
                                nearest_same_type_spacing_mm=round(distance) if distance else 'Single terminal',
                                indicative_half_spacing_throw_m=round(distance/2000,3) if distance and t['air_type']=='SA' else 'Room coverage required',
                                selection_criterion='Check isothermal / cooling throw at 0.25 m/s terminal velocity, occupied-zone draught and ADPI with actual ceiling / room dimensions',
                                proposed_noise_target='NC <=30 meeting / bed / operator; NC <=35 other occupied rooms; owner / acoustic consultant to confirm',
                                OEM_model='TBC',OEM_pressure_loss_pa='TBC',OEM_throw_m='TBC',OEM_NC='TBC',status='Duty / neck velocity verified; no catalogue performance claim'))
    write('Terminal_performance_Rev12.csv',performance)
    instruments=[]
    for i,r in enumerate(read('Instruments.csv'),1):
        tag=r['tag'];prefix=tag.split('-')[0];io=r['io']
        ranges={'TT':'0..50 degC','RHT':'0..100 %RH','DPT':'Room: -100..+100 Pa; fan: 0..1000 Pa','PDT':'0..1000 Pa','PDI':'0..1000 Pa','FIT':'0..5000 L/s','VS':'0..25 mm/s RMS','TSHH':'OEM heater manual-reset trip','AFS':'OEM flow-proof setpoint','EM':'Feeder voltage / CT ratio / protocol per approved electrical design'}
        mounting='Room sensor at +1.5 m AFFL away from supply jet / sunlight / heat source' if 'GF-' in tag or tag=='TT-B1-01' else 'At selected equipment / duct; tag references D-012 to D-016'
        taps='Not applicable'
        if prefix=='DPT' and ('GF-' in tag or 'B1-01'==tag[-5:]):taps='(+) room static; (-) sheltered outdoor reference, common datum; prevent wind bias'
        elif prefix in ['DPT','PDT','PDI']:taps='(+) upstream; (-) downstream; separate labelled static taps and isolation / test ports; no facing-flow pickup'
        elif prefix=='FIT':taps='OEM measurement array / station; reserve 5Dh upstream and 3Dh downstream as screening allowance, not approved OEM minimum'
        wire='Shielded twisted pair, 4-20 mA proposed; separate from power, shield earth at panel end; supply / isolator per OEM' if io=='AI' else 'Dry contact to DI proposed; OEM voltage / contact logic and final terminal IDs TBC' if io=='DI' else 'Local indication; no PLC channel' if io=='LOCAL' else 'Meter communication: protocol / address / isolation / termination TBC'
        safety='Hardwired heater safety chain; PLC demand cannot override AFS or independent high-limit; confirmed fire stops fans / heaters, manual reset' if prefix in ['TSHH','AFS'] else 'Alarm settings, scaling and response approved during commissioning'
        instruments.append(dict(tag=tag,location=r['location'],IO=io,proposed_range=ranges.get(prefix,'OEM to select'),
                                mounting_detail=mounting,pressure_taps_or_straight_length=taps,wiring_proposal=wire,
                                access='Maintain visible tag, reachable isolation / test / reset and equipment removal path; mounting-specific clearance per OEM',
                                safety_or_commissioning=safety,detail='D-028 / D-029',status='Proposed installation specification; OEM wiring and panel terminal numbers pending'))
    write('Instrument_installation_Rev12.csv',instruments)
    envelopes=[]
    for r in sections:
        depth=float(r['height_mm'] or r['diameter_mm']);top=3400+depth+50
        envelopes.append(dict(component=r['tag'],type='Duct with insulation / proposed 25 mm flange each side',
                              lowest_reserved_mm_affl=3325,highest_reserved_mm_affl=top+25,
                              ceiling_clearance_mm=25,slab_clearance_mm=4000-top-25,
                              status='Duct plus flange allowance only; actuator / hanger and beam conflicts checked separately at shop stage'))
    for r in read('Components.csv'):
        if r['tag'].startswith('EH-') and r['tag']!='EH-COM-01':
            envelopes.append(dict(component=r['tag'],type='Room heater procurement limit',lowest_reserved_mm_affl=3350,highest_reserved_mm_affl=3850,
                                  ceiling_clearance_mm=50,slab_clearance_mm=150,
                                  status='Casing INCLUDING insulation must fit 500 mm overall height; outlet / high-limit / airflow-proof access per OEM, otherwise relocate'))
    write('Installation_envelopes_Rev12.csv',envelopes)
    result={'roof_routes':len(roof),'roof_crossings':len(crosses),'roof_conflicts':conflicts,'roof_curbs':len(curbs),'roof_support_reservations':len(support),
            'pressure_paths':len(paths),'fitting_allowances':len(fittings),'instrument_installation_rows':len(instruments),'terminal_performance_rows':len(performance),
            'supply_l_s':sa,'return_l_s':ra,'known_extract_l_s':ea,'minimum_mass_balance_makeup_l_s':sa-ra,
            'unallocated_exfiltration_less_CAG_extract_l_s':sa-ra-ea,'OA_reference_shortfall_l_s':sa-ra-420.7,
            'fan_budgets':fans,'basis':basis,'scope':'Connected roof routing proposal; provisional levels / loads / K / OEM selections; not construction approved'}
    (BASE.parent/'engineering_rev12.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':print(json.dumps(generate()))
