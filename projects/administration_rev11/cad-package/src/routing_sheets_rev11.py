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
        for r in g['RISERS']:
            if r['air_type']!=air or (rooms is not None and r['room'] not in rooms):continue
            xx,yy=float(r['x_mm']),float(r['y_mm'])
            if bounds[0]+200<xx<bounds[2]-200 and bounds[1]+200<yy<bounds[3]-200:
                xy=P(xx,yy);s.circle(*xy,120,air,9,'#FFFFFF')
                s.line([(xy[0]-80,xy[1]-80),(xy[0]+80,xy[1]+80)],air,7)
                s.line([(xy[0]-80,xy[1]+80),(xy[0]+80,xy[1]-80)],air,7)
                q={'air':air,'block':'HVAC_AD','xy':xy,'width':float(r['width_mm']),'angle':0,'tag':r['tag']}
                g['annotate_station'](s,q,r['tag'],label_boxes,services=[air],bounds=clip,z=100)
        return s,bounds

    s=frame('ACTUAL DUCT JUNCTIONS - ENLARGED PLAN DETAILS',19,scale='AS SHOWN')
    cases=[('A','SA',(4900,16800),'GF-02 ROOF DROP / BRANCH / HEADER LEGS',['02'],20),
           ('B','SA',(5000,13100),'GF-02 END TEE / TWO INDIVIDUAL NECKS',['02','05'],25),
           ('C','SA',(2900,4300),'MEETING CONTINUING HEADER / SIDE NECK',['04'],20),
           ('D','SA',(8500,5600),'TELECOM FEEDER / UP AND DOWN HEADERS',['08'],20),
           ('E','SA',(12500,10200),'CORRIDOR ROOM DROP BRANCH / HEATER / HEADER',['06'],20),
           ('F','RA',(11300,9250),'CORRIDOR COLLECTION / RETURN DEVICE STATION',['06'],20)]
    for i,(label,air,center,title,rooms,den) in enumerate(cases):
        x=18+(i%3)*270;y=42+(i//3)*230
        heading(s,x,y,label+'  '+title+' / 1:'+str(den),260)
        model,bounds=detail(air,center,rooms,width=260*den,height=160*den)
        name='JUNCTION_'+label;models[name]=model
        g['view'](s,model,x,y+12,den,bounds)
        s.para(x,y+179,'Actual Rev11 duct envelope; connected inside seams removed. Individual clear sizes and neck duties: Duct_sections / Terminals registers.',258,2.5)
        s.para(x,y+199,'Formed fitting / access / face-to-face dimensions require selected manufacturer confirmation. Other services omitted in this enlargement; single-layer envelope on D-020, roof drops on D-022.',258,2.4,'NOTE')
    g['note_footer'](s,'These details are generated from the delivered routing geometry, not independent typical symbols. Continuous exteriors, flared necks and concave fitting throats are checked. Short necks use an integral plenum / vertical drop; their selected construction is pending.')
    sheets.append(s)

    s=frame('3.30 m CEILING - SINGLE-LAYER INDOOR DUCT ENVELOPE',20)
    heading(s,18,43,'USER DATUMS AND PROPOSED INDOOR LEVELS',460)
    data=[['Structural underside','+4.000 m AFFL','User confirmed slab / roof'],
          ['Minimum ceiling / clear height','+3.300 m AFFL','User requirement'],
          ['Available total space','700 mm','Between confirmed datums'],
          ['Proposed bare duct bottom','+3.400 m AFFL','All indoor trees; not installed'],
          ['Indoor insulation','50 mm each face','Assumed; project specification TBC'],
          ['Largest bare duct depth','400 mm','Round necks max D350 retained'],
          ['Lowest insulated bottom','+3.350 m AFFL','50 mm above required ceiling'],
          ['Highest insulated top','+3.850 m AFFL','150 mm below slab for deepest duct']]
    yy=table(s,18,52,460,['Item','Value','Basis / status'],data,[1.5,1.1,1.6],2.8,24)
    heading(s,18,yy+16,'WHAT THE REVISED ROUTES RESOLVE',460)
    yy+=31
    for t in ['Deep common mains move to a proposed roof distribution system. Fifteen independent room supply / return drops replace the indoor common-main feeders.',
              'Electrical and telecom returns collect at room perimeters. Every room tree is connected, every collection node conserves airflow, and distinct room trees stay separate.',
              'No indoor bare duct crossings or insulated separate-service overlaps. Continuous duct walls, formed junctions and individual terminal necks are generated from the real revised plan geometry.',
              'Rev10 CX-08 had its lowest insulated bottom at +2.050 m, 1250 mm below this requirement. The Rev10 stacked arrangement is superseded by this roof option; it must not be installed at a 3.30 m ceiling.']:
        yy+=s.para(18,yy,t,454,2.8)+9
    heading(s,511,43,'DEEPEST DUCT ENVELOPE - NTS',308)
    s.line([(525,95),(812,95)],'ARCH',.6)
    s.text(525,88,'SLAB / ROOF UNDERSIDE +4.000 m',2.9,'INK',True)
    s.rect(562,135,184,80,'SA',.5,'#FFFFFF')
    s.rect(552,125,204,100,'DIM',.3,None,True)
    s.text(654,171,'BARE DUCT DEPTH 400 mm',3.1,'SA',True,'center')
    s.text(654,189,'W PER SECTION REGISTER',2.7,'SA',align='center')
    s.line([(525,235),(812,235)],'INK',.5)
    s.text(525,250,'CEILING / CLEAR HEIGHT +3.300 m',2.9,'INK',True)
    for y,t in [(119,'150 mm slab allowance'),(134,'50 mm insulation'),(214,'Bare BOD +3.400 m'),(227,'Insulated bottom +3.350 m')]:s.text(760,y,t,2.4,'NOTE',align='left')
    s.para(511,279,'Stack: 150 mm slab / support allowance + 50 mm insulation + 400 mm bare duct + 50 mm insulation + 50 mm ceiling gap = 700 mm.',302,3,'INK',True)
    s.para(511,326,'This checks scheduled duct envelopes only. Beam downstands, other services, flanges / stiffeners, damper actuators, heater casing, supports, access hatches and terminal plenums are not manufacturer-selected or surveyed.',302,2.9)
    s.para(511,391,'The 50 mm gap below insulation is not a general maintenance clearance or a selected plenum dimension. Terminal drops / plenums must use the available connection space within the duct envelope; selected assemblies may require a local redesign.',302,2.9)
    s.para(511,454,'Roof option selection pending. Do not cut the slab from these drawings. New penetrations, curbs, weatherproofing, roof loads and fire boundaries require structural / architectural / fire coordination.',302,2.9,'INK',True)
    g['note_footer'](s,'PROPOSED LEVELS, NOT INSTALLATION APPROVAL. AFFL datum requires site confirmation. 50 mm insulation is an indoor assumption, not a verified UAE standard. D-022 identifies all proposed roof drops; actual roof routing and equipment envelopes remain open.')
    sheets.append(s)

    s=frame('REV11 TERMINAL MOVES AND SHALLOW DUCT SIZE CHANGES',21)
    changes=rows('Rev11_terminal_changes.csv');resized=rows('Rev11_size_changes.csv')
    heading(s,18,43,'PROPOSED TERMINAL MOVES FROM REV10',442)
    table(s,18,52,442,['Terminal','Rev10 X, Y mm','Rev11 X, Y mm','L/s'],[[r['tag'],r['old_x_mm']+', '+r['old_y_mm'],r['new_x_mm']+', '+r['new_y_mm'],r['flow_l_s']] for r in changes],[1.2,1.6,1.6,.7],2.6,17)
    s.para(18,302,'Individual duties, neck diameters and face sizes are retained. Moves make room for perimeter return trees and insulation; coordinate reflected ceiling, throw / noise, lighting and maintenance access before adoption.',436,2.9)
    heading(s,18,370,'TRACEABLE ROUTING / AIRFLOW',442)
    s.para(18,385,f"{len(g['SECTIONS'])} indoor section paths; 15 proposed roof drops. Local branches, headers and necks remain connected to their allocated room riser. Roof-main sizes / flows are separately listed as a functional basis; actual roof lengths and levels are TBC.",436,2.9)
    s.para(18,445,'All indoor section velocities, plan centerline lengths and straight-duct friction are recomputed. Wider shallow sections replace the deep returns. Selected elbow / riser / transition losses and revised total fan ESP remain pending; straight friction is not a system pressure calculation.',436,2.9)
    heading(s,486,43,'CLEAR SIZE REVISIONS FROM REV10',334)
    yy=table(s,486,52,334,['Section','Rev10 mm','Rev11 mm'],[[r['tag'],r['previous_size_mm'],r['revised_size_mm']] for r in resized],[1.3,1,1],2.6,15)
    s.para(486,yy+16,'Largest indoor bare depth: 400 mm. Outdoor common mains retain their flow / clear-size basis; weather insulation, actual roof routes and fitting / level selection are pending.',330,2.9)
    s.para(486,yy+76,'85 instrument requirements and all existing I/O duties are retained. Common heater / probes / conditional humidifier move to the proposed roof plant, with weather-protected equipment and mounting still to be selected.',330,2.9)
    g['note_footer'](s,'Rev11 is a roof-distribution OPTION developed for the new 3.30 m clear-height requirement. Rev10 remains preserved as superseded for this ceiling constraint. These are engineering coordination proposals; final ceiling / OEM / pressure / structural approvals are pending.')
    sheets.append(s)

    s=frame('ROOF DISTRIBUTION OPTION AND ROOM RISER REGISTER',22)
    heading(s,18,43,'FUNCTIONAL ROOF CONNECTIONS - NTS / ACTUAL ROOF ROUTING TBC',804)
    s.line([(35,86),(803,86)],'SA',.6);s.arrow((35,86),(72,86),'FLOW',.3,2)
    s.text(35,73,'SUPPLY FROM ROOF COMMON PLANT D-008 / 3697.80 L/s',2.8,'SA',True)
    for i,rid in enumerate(g['ORDER']):
        x=80+i*81;s.line([(x,86),(x,113)],'SA',.4)
        s.rect(x-34,113,68,27,'SA',.3,'#FFFFFF')
        s.text(x,123,'GF-'+rid+' / RS-SA'+rid,2.5,'SA',align='center')
        s.text(x,134,f"{g['ROOMS'][rid]['sa']:.2f} L/s",2.5,'SA',align='center')
    s.text(35,159,'Separate supply drops connect to each room VCD / conditional MFD / heater station; no ceiling common main.',2.8)
    s.line([(35,208),(803,208)],'RA',.6);s.arrow((72,208),(35,208),'FLOW',.3,2)
    s.text(35,195,'RETURN TO ROOF COMMON PLANT D-008 / 3006.68 L/s ASSUMED',2.8,'RA',True)
    for i,rid in enumerate([r for r in g['ORDER'] if g['ROOMS'][r]['rn']]):
        x=100+i*132;s.line([(x,208),(x,235)],'RA',.4)
        s.rect(x-55,235,110,27,'RA',.3,'#FFFFFF')
        s.text(x,245,'GF-'+rid+' / RS-RA'+rid,2.5,'RA',align='center')
        s.text(x,256,f"{g['ROOMS'][rid]['ra']:.2f} L/s",2.5,'RA',align='center')
    heading(s,18,291,'PROPOSED ROOF DROP CENTERS - SOURCE PLAN X / Y, mm',804)
    table(s,18,300,804,['Riser','Branch / GF','X, Y mm','Clear W x H','L/s','Indoor bare BOD','Roof level / vertical length'],[[r['tag'],r['branch']+' / '+r['room'],str(r['x_mm'])+', '+str(r['y_mm']),r['width_mm']+'x'+r['height_mm'],f"{float(r['flow_l_s']):.2f}",'+3.400 m','TBC / TBC'] for r in g['RISERS']],[1,1.35,1.3,1.1,.8,1.15,1.75],2.7,11.4)
    s.para(18,491,'Roof flow/size basis is functional, not a fabricated plan: no roof survey, beam map, selected curb / sleeve / fire assembly or common heater weather enclosure was supplied. All 15 penetrations are proposals; coordinate spacing, framing, access and roof drainage before setting them out.',802,2.8)
    g['note_footer'](s,'DESIGN OPTION SELECTION PENDING. Do not treat this functional schematic as a physical roof routing / clash clearance drawing. The indoor plan is geometrically checked; roof branches, levels, insulation, lengths, losses, support loads and OEM clearances remain to be designed from site information.')
    sheets.append(s)
