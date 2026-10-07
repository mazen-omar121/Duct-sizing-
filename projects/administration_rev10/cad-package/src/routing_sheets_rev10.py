"""Actual geometry enlargements, crossing coordination and revision schedules."""
import csv
from shapely.geometry import box
from duct_geometry import pieces
from shapely.ops import unary_union


def append_sheets(g):
    Scene, network, P = g['Scene'], g['NETWORK'], g['P']
    sheets, models = g['SHEETS'], g['MODELS']
    frame, heading, table = g['paper_frame'], g['section_heading'], g['table']
    def rows(name):
        with (g['BASE']/'schedules'/name).open() as f:return list(csv.DictReader(f))

    def detail(air, center, rooms, width=5200, height=3200):
        x,y=center; mh=g['MH'];s=Scene(24500,mh)
        bounds=(x-width/2,y-height/2,x+width/2,y+height/2)
        clip=box(bounds[0],mh-bounds[3],bounds[2],mh-bounds[1])
        selection=unary_union([network.polygons[r['tag']] for r in g['SECTIONS'] if r['air_type']==air and (rooms is None or r['room'] in rooms or r['role']=='Main')]).buffer(.1)
        for edge in pieces(network.envelopes[air].boundary.intersection(clip).intersection(selection),'LineString'):
            s.line(list(edge.coords),air,13)
        for r in g['SECTIONS']:
            if r['air_type']!=air or (rooms is not None and r['room'] not in rooms and r['role']!='Main'):continue
            for a,b in zip(network.original[r['tag']],network.original[r['tag']][1:]):
                if clip.contains(box(min(a[0],b[0])-1,min(a[1],b[1])-1,max(a[0],b[0])+1,max(a[1],b[1])+1)):
                    length=((b[0]-a[0])**2+(b[1]-a[1])**2)**.5
                    if length>800:s.arrow((a[0]+.3*(b[0]-a[0]),a[1]+.3*(b[1]-a[1])),(a[0]+.42*(b[0]-a[0]),a[1]+.42*(b[1]-a[1])),'FLOW',9,60)
        for t in g['TERMINALS']:
            if t['air_type']!=air or (rooms is not None and t['room'] not in rooms):continue
            xx,yy=float(t['x_mm']),float(t['y_mm'])
            if bounds[0]+320<xx<bounds[2]-320 and bounds[1]+400<yy<bounds[3]-400:
                s.block({'SA':'HVAC_SD_4WAY','RA':'HVAC_RG'}[air],*P(xx,yy),sx=float(t['face_w_mm'])/(600 if air=='SA' else 500),tag=t['tag'])
                s.text(*P(xx,yy+570),t['tag']+' / D'+t['neck_dia_mm'],100,air,align='center',mask=True)
        label_boxes=[]
        for q in g['STATIONS']:
            if q['air']!=air or (rooms is not None and q['room'] not in rooms):continue
            xx,yy=q['xy'][0],mh-q['xy'][1]
            if bounds[0]+500<xx<bounds[2]-500 and bounds[1]+450<yy<bounds[3]-450:
                s.block(q['block'],*q['xy'],a=q['angle'],sy=1 if q['block']=='HVAC_AD' else q['mirror']*q['width']/600,tag=q['tag'])
                g['restore_device_walls'](s,q)
                g['annotate_station'](s,q,q['tag'],label_boxes,services=[air],bounds=clip,z=100)
        return s,bounds

    s=frame('ACTUAL DUCT JUNCTIONS - ENLARGED PLAN DETAILS',19,scale='AS SHOWN')
    cases=[('A','SA',(4800,16600),'GF-02 BRANCH / TWO HEADER LEGS',['02'],20),
           ('B','SA',(5000,13100),'GF-02 END TEE / TWO INDIVIDUAL NECKS',['02','05'],25),
           ('C','SA',(2900,4300),'MEETING CONTINUING HEADER / SIDE NECK',['04'],20),
           ('D','SA',(8500,5600),'TELECOM FEEDER / UP AND DOWN HEADERS',['08'],20),
           ('E','SA',(12500,10500),'CORRIDOR COMMON BRANCH / HEATER / HEADER',None,20),
           ('F','RA',(11300,8600),'CORRIDOR COLLECTION / RETURN DEVICE STATION',None,20)]
    for i,(label,air,center,title,rooms,den) in enumerate(cases):
        x=18+(i%3)*270;y=42+(i//3)*230
        heading(s,x,y,label+'  '+title+' / 1:'+str(den),260)
        model,bounds=detail(air,center,rooms,width=260*den,height=160*den)
        name='JUNCTION_'+label;models[name]=model
        g['view'](s,model,x,y+12,den,bounds)
        s.para(x,y+179,'Actual Rev10 duct envelope; connected inside seams removed. Individual clear sizes and neck duties: Duct_sections / Terminals registers.',258,2.5)
        s.para(x,y+199,'Formed fitting / access / face-to-face dimensions require selected manufacturer confirmation. Other services omitted in this enlargement; coordinate CX references on D-020.',258,2.4,'NOTE')
    g['note_footer'](s,'These details are generated from the delivered routing geometry, not independent typical symbols. Continuous exteriors, flared necks and concave fitting throats are checked. Short necks use an integral plenum / vertical drop; their selected construction is pending.')
    sheets.append(s)

    s=frame('DUCT CROSSING REGISTER AND VERTICAL COORDINATION',20)
    crossing=network.crossing_register()
    heading(s,18,43,'NUMBERED SEPARATE-SERVICE CROSSINGS / D-001 TO D-006',474)
    data=[[r['tag'],r['upper']+' / '+r['lower'],r['upper_sections'],r['lower_sections'],f"{r['x_mm']:g}, {r['y_mm']:g}"] for r in crossing]
    table(s,18,52,474,['CX','Upper / lower*','Upper duct sections','Lower duct sections','X, Y mm'],data,[.6,.85,2,2,1.25],2.4,16)
    s.para(18,400,'* Proposed vertical order, not verified installed levels. Every crossing requires BOD, ceiling / structure, insulation and support clearance to be coordinated. No same-service intersection is concealed by this convention.',474,2.7)
    s.para(18,431,f'Dashed lower-service edges are limited to the actual overlap footprint. The upper duct remains continuous. CX-01 through CX-{len(crossing):02d} are searchable in CAD, PDF and Excel.',474,2.7)
    s.para(18,468,'Structural underside: +4.000 m, user confirmed. Insulation: 50 mm indoor coordination assumption. Every crossing register includes the required stack and maximum local BOD bounds; these are not assigned duct elevations.',474,2.7)
    worst=min(crossing,key=lambda r:r['lowest_insulated_surface_mm_affl'])
    heading(s,516,43,worst['tag']+' HEIGHT ENVELOPE - NTS / HOLD',304)
    hu,hl=worst['upper_depth_mm'],worst['lower_depth_mm'];ub,lb=worst['upper_max_local_bod_mm_affl'],worst['lower_max_local_bod_mm_affl']
    s.line([(526,80),(815,80)],'ARCH',.4)
    s.text(526,75,'STRUCTURAL UNDERSIDE +4.000 m (USER)',2.7,'INK',True)
    s.rect(580,95,166,hu/10,'SA',.5);s.rect(575,90,176,hu/10+10,'SA',.25,dash=True)
    s.text(663,127,worst['upper_sections'],3,'SA',True,'center')
    s.text(663,144,f'UPPER DEPTH {hu:g} mm',2.7,'SA',align='center')
    yy=95+hu/10+20
    s.rect(580,yy,166,hl/10,'RA',.5);s.rect(575,yy-5,176,hl/10+10,'RA',.25,dash=True)
    s.text(663,yy+35,worst['lower_sections'],3,'RA',True,'center')
    s.text(663,yy+52,f'LOWER DEPTH {hl:g} mm',2.7,'RA',align='center')
    s.text(756,95+hu/10,f'+{ub/1000:.3f} MAX BOD',2.4,'SA')
    s.text(756,yy+hl/10,f'+{lb/1000:.3f} MAX BOD',2.4,'RA')
    s.para(516,304,'ASSUMED: 50 mm external insulation each duct; 100 mm gap between insulation; 100 mm structure / hanger allowance.',300,2.7)
    s.para(516,340,'Required stack: '+str(int(worst['required_stack_mm']))+' mm. Lowest insulated surface: +'+f"{worst['lowest_insulated_surface_mm_affl']/1000:.3f}"+' m under those assumptions. Check finished ceiling and access before selecting any level.',300,2.9,'INK',True)
    s.para(516,394,'CX-08 needs a shallower crossing section or reroute if the finished ceiling / access allowance cannot fit below this envelope. Recalculate width, velocity, transitions and fitting losses for the selected solution.',300,2.8)
    s.para(516,449,'All BODs remain TBC. Local bounds are not a connected-network elevation design. Insulation is an explicit assumption, not a verified UAE standard. Actual beams, supports, OEM clearances and terminal plenums are not surveyed.',300,2.7)
    g['note_footer'](s,'COORDINATION HOLD: 4.000 m structural underside confirmed; finished ceiling and duct BOD remain unassigned. Maximum local elevation bounds are calculated, not approved. Check the full crossing register and resolve CX-08 before construction.')
    sheets.append(s)

    s=frame('REV10 TERMINAL MOVES AND DUCT SIZE CHANGES',21)
    changes=rows('Rev10_terminal_changes.csv')
    heading(s,18,43,'PROPOSED TERMINAL RELOCATIONS - ROOM DUTIES UNCHANGED',444)
    table(s,18,52,444,['Terminal','Old X, Y mm','New X, Y mm','L/s'],
          [[r['tag'],r['old_x_mm']+', '+r['old_y_mm'],r['new_x_mm']+', '+r['new_y_mm'],f"{float(r['flow_l_s']):.2f}"] for r in changes],
          [1.15,1.6,1.6,.7],2.5,14)
    s.para(18,390,'The revised points are proposals. Coordinate all grille / diffuser faces against the reflected ceiling plan, lighting, access, throws and noise. Corridor terminals are returned to the corridor arrangement. Individual air duties, neck sizes and instrument allocations remain unchanged.',440,2.7)
    resized=rows('Rev10_size_changes.csv')
    heading(s,486,43,'PROPOSED CLEAR DUCT SIZE REVISIONS',334)
    table(s,486,52,334,['Section','Rev09 mm','Rev10 mm'],[[r['tag'],r['previous_size_mm'],r['revised_size_mm']] for r in resized],
          [1.25,1,1],2.5,10.5)
    y=78+10.5*len(resized)
    s.para(486,y,'Narrower / deeper sections separate the plan tracks. Areas and velocities are recalculated; the largest proposed depth is 800 mm. Available ceiling space, both height and width transitions, selected loss coefficients and fan ESP require verification.',330,2.7)
    heading(s,486,y+64,'ROUTING AND GEOMETRY CHECKS',334)
    summary=[f"{len(g['SECTIONS'])} scheduled section paths; every joint conserves its registered airflow.",
             'No duplicated same-service centerline and no unintended same-service polygon intersection.',
             'Separate main / corridor collection tracks; shared runs are sized headers, not coincident individual runouts.',
             'Continuous service exteriors; tapers replace the original throat; local formed fitting radii are shown.',
             f"{len(crossing)} separate-service crossings are indexed on D-020; elevations remain pending.",
             '85 instrument tags and the existing I/O duties are retained.']
    yy=y+78
    for t in summary:yy+=s.para(486,yy,t,330,2.7)+7
    g['note_footer'](s,'REV10 replaces the Rev09 routing proposal. The full path-by-path change log is in Excel / CSV; proposed terminal moves and size changes above require engineering coordination. Engineering approval, final levels and catalogue selections are pending.')
    sheets.append(s)
