"""Rev10 drafting improvements and complete, explicitly tagged I&C diagrams.

Room duties and I/O requirements are retained; Rev10 routing is revised; diagrams do not establish OEM wiring,
terminal numbers, elevations, setpoints, pressure performance or fabrication.
"""
from math import hypot, pi
import csv
import json


def enhance(g):
    Scene, sheets = g['Scene'], g['SHEETS']
    frame, heading, table = g['paper_frame'], g['section_heading'], g['table']
    pd, bs, footer = g['pd'], g['bs'], g['note_footer']
    instruments = {r['tag']: r for r in g['INSTRUMENTS']}
    covered = set()
    references = {}
    for i, sheet in enumerate(sheets, 1):
        for op in sheet.ops:
            if op[0] == 'block' and op[-1] in instruments:
                covered.add(op[-1]); references.setdefault(op[-1], set()).add(i)
            if op[0] == 'text' and op[3] in instruments:
                covered.add(op[3]); references.setdefault(op[3], set()).add(i)
    for name, scene in g['MODELS'].items():
        for op in scene.ops:
            if op[0] == 'block' and op[-1] in instruments:
                covered.add(op[-1]); references.setdefault(op[-1], set()).add(7)

    def bubble(s, x, y, tag, sheet, r=5.5):
        assert tag in instruments, tag
        covered.add(tag); references.setdefault(tag, set()).add(sheet)
        s.circle(x, y, r, 'INST', .25, '#FFFFFF')
        prefix, suffix = tag.split('-', 1)
        s.line([(x-r*.85, y), (x+r*.85, y)], 'INST', .18)
        s.text(x, y-1.2, prefix, 2.3, 'INST', True, 'center')
        s.text(x, y+3.2, suffix, min(1.9, 14/max(1,len(suffix))), 'INST', False, 'center')
        s.text(x, y-r-2.2, tag, 2.5, 'INST', False, 'center')
        return x, y

    def signal(s, points, io='AI', label=True):
        s.line(points, 'INST', .18, True)
        if label:
            x,y=points[-1];s.text(x-1,y-2.4,io,2.2,'INST',False,'right')

    def tap(s, x, y):
        s.circle(x,y,.6,'INST',.18,'#FFFFFF')

    # Room sensors now show the signal destination and outdoor DP references,
    # rather than relying solely on rows of instrument bubbles.
    sc = g['MODELS']['INSTRUMENTATION']
    original_ops = len(sc.ops)
    positions = {'02':(5700,15100),'05':(14600,16700),'04':(2200,5000),
                 '08':(8700,5150),'06':(6700,9450),'07':(13800,2700),
                 '09':(13200,6350),'03':(18800,6100),'01':(18100,2800)}
    P=g['P']
    for rid,(x,y) in positions.items():
        # One per-room signal trunk is diagrammatic, not a cable route.
        for dx in [-1100,0,1100]:
            sc.line([P(x+dx,y-150),P(x+dx,y-950)],'INST',8,True)
        sc.line([P(x-1100,y-950),P(x+1100,y-950)],'INST',8,True)
        sc.text(*P(x,y-1270),'3 AI TO HPCP-01 / D-015',130,'INST',align='center',mask=True)
        # Actual reference tube route is shown in the installation detail only.
        sc.line([P(x+1250,y),P(x+1700,y),P(x+1700,y-260)],'INST',8)
        sc.text(*P(x+1700,y-520),'(-) OUTDOOR REF.',110,'INST',align='center',mask=True)
    # Plan view blocks were copied when D-007 was composed; update those copies.
    for name, scene in g['MODELS'].items():
        if name.startswith('INSTRUMENTATION_'):
            scene.ops.extend(sc.ops[original_ops:])

    # Enlargements carry terminal neck and flow beside the plotted terminal tag.
    terminal_aliases={}
    for terminal in g['TERMINALS']:
        prefix,room,number=terminal['tag'].split('-')
        terminal_aliases[f'{prefix}{room}-{int(number)}']=terminal
    viewport_bounds={id(op[1]):op[5] for sheet in sheets for op in sheet.ops if op[0]=='place'}
    for name, scene in g['MODELS'].items():
        if not name.startswith(('NORTH_DETAIL','SOUTH_DETAIL')):
            continue
        additions=Scene(fontscale=1)
        for op in scene.ops:
            if op[0]!='text' or op[3] not in terminal_aliases:
                continue
            terminal=terminal_aliases[op[3]]
            flow=g['num'](terminal['flow_l_s'])
            neck='D'+terminal['neck_dia_mm'] if terminal['neck_dia_mm']!='TBC' else 'NECK TBC'
            details=neck+' / '+(f'{flow:.1f} L/s' if flow is not None else 'FLOW TBC')
            additions.text(op[1],op[2]+op[4]*1.4,details,op[4]*.85,op[5],align=op[7],mask=True)
            bounds=viewport_bounds.get(id(scene))
            if bounds:
                text_box=g['text_bounds'](additions.ops[-1])
                if not (text_box[0]>=bounds[0] and text_box[1]>=bounds[1]
                        and text_box[2]<=bounds[2] and text_box[3]<=bounds[3]):
                    del additions.ops[-2:]
        scene.ops.extend(additions.ops)

    # D-013: every extract / basement fan is individually identified.
    s=frame('EXTRACT AND BASEMENT FAN INSTRUMENTATION',13)
    fans=['EF-03-01','EF-03-02','EF-09-01','EF-09-02','EF-01-01',
          'SF-B1-01','SF-B1-02','EF-B1-01','EF-B1-02']
    for i,fan in enumerate(fans):
        x=18+(i%3)*273;y=42+(i//3)*153
        s.rect(x,y,258,145,'DIM',.18)
        s.text(x+5,y+8,f'{i+1:02d}  {fan}',3.5,'INK',True)
        air='SA' if fan.startswith('SF') else 'EA'
        pd(s,[(x+15,y+71),(x+240,y+71)],10,air)
        bs(s,'HVAC_FLEX',x+73,y+71,3,10)
        bs(s,'HVAC_FAN',x+106,y+71,18,18)
        bs(s,'HVAC_MD',x+196,y+71,3,10)
        bubble(s,x+76,y+39,'DPT-'+fan,13)
        bubble(s,x+169,y+39,'VS-'+fan,13)
        for px,side in [(x+93,-1),(x+120,1)]:
            s.line([(px,y+71),(px,y+39),(x+76+side*5.5,y+39)],'INST',.18);tap(s,px,y+71)
        s.text(x+89,y+54,'-',2.4,'INST');s.text(x+121,y+54,'+',2.4,'INST')
        s.line([(x+169,y+44.5),(x+147,y+58),(x+113,y+66)],'INST',.18)
        signal(s,[(x+76,y+33.5),(x+76,y+23),(x+237,y+23)],label=False)
        signal(s,[(x+169,y+33.5),(x+169,y+23)],label=False)
        s.text(x+235,y+20,'AI / HPCP-01',2.3,'INST',False,'right')
        s.text(x+15,y+92,'INLET',2.4,'NOTE');s.text(x+196,y+92,'ISOLATION',2.4,'NOTE')
        s.para(x+5,y+109,'DP taps across fan. VS attachment at OEM bearing / frame. Isolation tag and fail position: approved control register.',248,2.5)
    footer(s,'NTS functional arrangements. Basement equipment positions are not shown on the Administration plan. CAG fan duty / quantity, tap locations, alarm limits and vibration mountings require OEM / I&C confirmation.')
    sheets.append(s)

    # D-014: six separate heater circuits, retaining all scheduled AFS / TSHH.
    s=frame('ELECTRIC HEATER PROTECTION AND CONTROL',14)
    heaters=['04','05','06','07','03','COM-01']
    for i,h in enumerate(heaters):
        x=18+(i%2)*409;y=42+(i//2)*153
        s.rect(x,y,394,145,'DIM',.18)
        s.text(x+5,y+8,'EH-'+h+'  |  SAFETY / MONITORING INTERFACE',3.2,'INK',True)
        pd(s,[(x+14,y+77),(x+375,y+77)],12,'SA')
        bs(s,'HVAC_EH',x+212,y+77,20,17)
        bs(s,'HVAC_AD',x+162,y+83,5,5)
        s.text(x+160,y+96,'AD-H'+h,2.5,'INK',False,'center')
        bubble(s,x+69,y+48,'AFS-EH-'+h,14)
        bubble(s,x+280,y+48,'TSHH-EH-'+h,14)
        s.line([(x+69,y+53.5),(x+69,y+77)],'INST',.18);tap(s,x+69,y+77)
        s.line([(x+280,y+53.5),(x+250,y+65),(x+222,y+77)],'INST',.18);tap(s,x+222,y+77)
        s.rect(x+111,y+16,125,18,'INK',.25,'#FFFFFF')
        s.text(x+173.5,y+23,'OEM HARDWIRED SAFETY CHAIN',2.6,'INK',True,'center')
        s.text(x+173.5,y+30,'HEATER ENABLE / CONTACTOR',2.4,'INK',False,'center')
        # Solid circuits = proposed physical safety interfaces; dashed = monitor.
        s.line([(x+69,y+42.5),(x+69,y+25),(x+111,y+25)],'INST',.25)
        s.line([(x+280,y+42.5),(x+280,y+25),(x+236,y+25)],'INST',.25)
        signal(s,[(x+69,y+48),(x+20,y+48),(x+20,y+20)],'DI')
        signal(s,[(x+280,y+48),(x+371,y+48),(x+371,y+20)],'DI')
        s.text(x+5,y+113,'LOSS OF PROOF / HIGH LIMIT: HEATING OFF',2.8,'INK',True)
        s.para(x+5,y+124,'PLC heat demand cannot override OEM safety. Sensor technology, setpoints, manual reset and terminal wiring: OEM / I&C approval.',384,2.5)
    footer(s,'Functional interfaces, not certified wiring diagrams. Six airflow-proof DI and six high-limit DI tags are retained. Protection circuits must be independently implemented and approved by the heater manufacturer.')
    sheets.append(s)

    # D-015: complete signal notation, all remaining basement / energy instruments.
    s=frame('FIELD SIGNALS, BASEMENT AND CONTROL INTERFACES',15)
    heading(s,18,44,'01  INSTRUMENT / SIGNAL CONVENTIONS',388)
    for i,(prefix,desc) in enumerate([('TT','Temperature transmitter'),('RHT','Humidity transmitter'),
                                    ('DPT','Differential pressure transmitter'),('FIT','Airflow transmitter'),
                                    ('PDT','Remote filter DP transmitter'),('PDI','Local differential pressure indication'),
                                    ('VS','Vibration sensing'),('AFS','Airflow proving switch'),
                                    ('TSHH','Heater high-temperature limit')]):
        y=58+i*13;s.circle(27,y,4.5,'INST',.25);s.text(27,y+1,prefix,2,'INST',True,'center');s.text(42,y+1,desc,2.8)
    s.line([(18,183),(75,183)],'INST',.25);s.text(84,184,'Sensing / physical interface (route schematic)',2.7)
    s.line([(18,196),(75,196)],'INST',.18,True);s.text(84,197,'Electrical / communications signal (schematic)',2.7)
    s.para(18,215,'AI / AO / DI / DO are point classes, not selected signal ranges. 4-20 mA, contacts, network protocol, cable types and terminal numbers are not inferred.',385,2.7)
    heading(s,18,257,'02  BASEMENT FIELD SENSING - PROPOSED',388)
    s.rect(26,278,363,105,'DIM',.18);s.text(34,289,'CABLE BASEMENT / B1',3.2,'INK',True)
    bubble(s,93,324,'TT-B1-01',15);bubble(s,232,324,'DPT-B1-01',15)
    signal(s,[(93,318.5),(93,301),(343,301)],label=False)
    signal(s,[(232,318.5),(232,301)],label=False)
    s.text(345,298,'AI TO HPCP-01',2.4,'INST',False,'right')
    s.line([(237.5,324),(276,324),(276,351),(353,351)],'INST',.18)
    s.text(251,319,'-',2.5,'INST');s.text(305,360,'OUTDOOR STATIC REF.',2.4,'INST',False,'center')
    s.text(217,346,'+ BASEMENT',2.5,'INST')
    s.para(26,397,'Basement temperature, volume, fan duties and actual pressure target remain open. Fan instrumentation is fully tagged on D-013; no basement architectural layout was supplied.',363,2.7)

    heading(s,427,44,'03  HPCP / HMI / BMS INTERFACE',394)
    s.rect(440,72,173,72,'INST',.25);s.text(526.5,87,'HPCP-01 / PLC',3.2,'INST',True,'center')
    s.text(526.5,100,'FIELD AI / AO / DI / DO',2.6,'INST',False,'center')
    s.text(526.5,113,'OEM SAFETY REMAINS INDEPENDENT',2.6,'INST',False,'center')
    s.text(526.5,130,'MODULE / CHANNEL ASSIGNMENTS TBC',2.5,'NOTE',False,'center')
    s.rect(661,72,148,35,'INST',.25);s.text(735,86,'HMI-01 / LOCAL OPERATOR',2.7,'INST',True,'center')
    s.text(735,99,'MIMIC / ALARMS / TRENDS',2.5,'INST',False,'center')
    signal(s,[(613,90),(661,90)],label=False)
    s.rect(661,124,148,36,'INST',.25);s.text(735,139,'BMS / SCADA',3,'INST',True,'center')
    s.text(735,152,'MONITOR / START / E-STOP',2.5,'INST',False,'center')
    signal(s,[(613,129),(637,129),(637,142),(661,142)],label=False)
    bubble(s,497,199,'EM-HPCP-01',15,r=7)
    signal(s,[(497,192),(497,144)],'COMM')
    s.para(524,190,'Feeder energy monitoring where motor rating exceeds 7.5 kW. Meter quantity, CT ratios and protocol require selection.',282,2.7)
    heading(s,427,244,'04  POINT CLASSES / MINIMUM SPARE',394)
    counts={t:sum(r['type']==t for r in g['IO']) for t in ['AI','AO','DI','DO']}
    from math import ceil
    table(s,427,253,394,['Class','Scheduled','20% spare','Min. channels'],
          [[t,n,ceil(n*.2),n+ceil(n*.2)] for t,n in counts.items()],[1,1,1.2,1.4],2.8,12)
    s.para(427,326,'COMM interfaces are separate from hardwired channels. Local PDI instruments have no PLC channel. Additional proposals are identified in the instrument index, D-016.',388,2.8)
    heading(s,427,381,'05  FIRE / STARTUP DESIGN INTENT',394)
    s.para(427,392,'Confirmed fire: stop every HVAC fan and heater. Restart after fire ESD requires local manual reset. Damper fire positions are governed by the approved cause-and-effect, not this drawing.',388,2.8)
    s.para(427,436,'Normal operation: two duty 50% PAUs with an available alternate. Prove selected air paths before starting fans. Duty rotation, changeover, timing and final permissives require approved OEM logic.',388,2.8)
    footer(s,'All controls shown are functional design intent. Approved OEM wiring and project I&C schedules govern implementation. D-016 provides an instrument-to-drawing cross-reference for every one of the 85 scheduled instruments.')
    sheets.append(s)

    # D-016: every instrument gets a specific drawing reference and status.
    assert covered == set(instruments), sorted(set(instruments)-covered)
    index=[]
    for tag,r in instruments.items():
        loc=r['location'].replace('Common supply straight length per manufacturer','Common SA').replace('Common return straight length per manufacturer','Common RA')
        loc=loc.replace('Electrical panel','Elec. panel').replace('Operator console','Operator').replace('Reception / corridor','Corridor').replace('Toilet group: two cubicles','Toilets').replace('Clean-agent cylinder room','Clean agent').replace('Bedroom / Resting Room','Rest room').replace('Kitchen / kitchenette','Kitchen').replace('Telecom panel','Telecom')
        provision = 'OEM safety' if 'OEM safety' in r['provision'] else 'Proposal' if 'proposal' in r['provision'].lower() or 'Proposed' in r['provision'] else 'Required*' if 'threshold' in r['provision'] else 'Required'
        ref=' / '.join(f'{i:03d}' for i in sorted(references[tag]))
        index.append({'tag':tag,'io':r['io'],'location':r['location'],'provision':r['provision'],'drawings':ref})
        r['_index']=[tag,r['io'],loc,provision,ref]
    s=frame('COMPLETE INSTRUMENT INDEX AND DRAWING REFERENCES',16)
    entries=list(instruments.values())
    for x,part in [(18,entries[:43]),(427,entries[43:])]:
        table(s,x,43,394,['Instrument tag','I/O','Service / location','Status','D-sheet'],
              [r['_index'] for r in part],[1.7,.45,2.4,1.0,.85],2.4,10.7)
    footer(s,'85 unique instruments: each has a tagged graphic and drawing reference. Proposal / OEM safety / conditional metering statuses are retained. D-sheet references are ADM-HVAC-D-nnn; local PDI instruments are not wired AI points.')
    sheets.append(s)
    with (g['BASE']/'schedules'/'Instrument_drawing_index.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['tag','io','location','provision','drawings']);writer.writeheader();writer.writerows(index)

    # D-017: native CAD dimensioning of known centerlines and endpoints.
    dims=[]
    def dim(scene,a,b,base,angle=0,z=145):
        display=Scene();horizontal=angle==0
        aa=(a[0],base[1]) if horizontal else (base[0],a[1])
        bb=(b[0],base[1]) if horizontal else (base[0],b[1])
        display.line([a,aa],'DIM',7);display.line([b,bb],'DIM',7);display.line([aa,bb],'DIM',9)
        for x,y in [aa,bb]:display.line([(x-z*.35,y-z*.35),(x+z*.35,y+z*.35)],'DIM',9)
        length=abs(b[0]-a[0]) if horizontal else abs(b[1]-a[1])
        if horizontal:display.text((aa[0]+bb[0])/2,base[1]-z*.6,f'{length:g}',z,'DIM',align='center')
        else:display.text(base[0]-z*.6,(aa[1]+bb[1])/2,f'{length:g}',z,'DIM',align='center',angle=90)
        scene.ops.append(('dimension',a,b,base,angle,z,display.ops));dims.append((a,b))
    layout=Scene(24500,g['MH']);g['architecture'](layout)
    for r in g['SECTIONS']:
        if r['role']=='Main':
            layout.line(g['pts'](r),r['air_type'],10,True)
            a,b=g['pts'](r)[0],g['pts'](r)[-1]
            layout.text(*a,r['tag'],140,r['air_type'],mask=True)
    for t in g['TERMINALS']:
        x,y=float(t['x_mm']),float(t['y_mm']);layout.block({'SA':'HVAC_SD_4WAY','RA':'HVAC_RG','EA':'HVAC_EG'}[t['air_type']],*P(x,y),sx=float(t['face_w_mm'])/(600 if t['air_type']=='SA' else 500),tag=t['tag'])
    for a,b in [(0,1800),(1800,3500),(3500,5700),(5700,20000)]:
        dim(layout,P(a,19500),P(b,19500),P(0,20300))
    dim(layout,P(0,19500),P(20000,19500),P(0,20900))
    for a,b in [(0,8225),(8225,9475),(9475,12525),(12525,16600),(16600,19500)]:
        dim(layout,P(0,a),P(0,b),P(-550,0),90)
    dim(layout,P(0,0),P(0,19500),P(-1100,0),90)
    # These are source plan coordinates, not surveyed structural datums.
    layout.circle(*P(0,0),140,'DIM',9)
    layout.text(*P(500,-100),'LOCAL ORIGIN (0,0)',130,'DIM')
    g['MODELS']['SETTING_OUT']=layout
    s=frame('PLAN DIMENSIONS AND TERMINAL SETTING-OUT',17,scale='1:50')
    g['view'](s,layout,28,42,50,(-1600,-700,23900,21400))
    heading(s,557,43,'SOURCE PLAN COORDINATES / DATUM',265)
    s.para(557,56,'Dimensions and coordinates are derived from the supplied architectural plan. Local (0,0) is a drawing origin, not a surveyed site benchmark. Confirm all setting-out against the coordinated ceiling and architecture.',260,2.8)
    rows=[]
    for rid in g['ORDER']:
        terms=[t for t in g['TERMINALS'] if t['room']==rid]
        xs=[float(t['x_mm']) for t in terms];ys=[float(t['y_mm']) for t in terms]
        rows.append([rid,f'{min(xs):g} - {max(xs):g}',f'{min(ys):g} - {max(ys):g}'])
    table(s,557,108,265,['GF','Terminal X range mm','Terminal Y range mm'],rows,[.5,1.5,1.5],2.6,14)
    s.para(557,262,'Individual terminal coordinates: Terminals register. Main centerlines: Duct_sections register. Native CAD dimensions are provided for the known overall extents and main offsets.',260,2.8)
    s.para(557,305,'Structural underside is +4.000 m (user confirmed). External insulation 50 mm is an indoor coordination assumption. Duct BOD and finished ceiling remain TBC. D-020 records the crossing stack limits and CX-08 height hold.',260,2.8)
    heading(s,557,367,'INSPECTION / COORDINATION NOTES',265)
    for i,text in enumerate(['Verify dimensions on site; do not scale NTS details.',
                             'Match device tags to registers before procurement.',
                             'Reserve access to dampers, heaters and filters.',
                             'Obtain selected-fitting losses and OEM duties.',
                             'Close pressure / outdoor-air design holds.'],1):
        s.para(557,380+(i-1)*12,f'{i}. {text}',260,2.8)
    footer(s,'Dimension chains are plan centerline offsets and architectural extents only. They are not approved fabrication, support or vertical-clearance dimensions. Terminal faces retain scheduled dimensions; final catalogue free areas and performance remain pending.')
    sheets.append(s)

    # D-018: sheet index and compact, discipline-specific issue conventions.
    s=frame('DRAWING INDEX, DESIGN BASIS AND ISSUE NOTES',18)
    rows=[]
    for i,sheet in enumerate(sheets,1):
        title=next(op[3].replace('ADMINISTRATION BUILDING - ','') for op in sheet.ops if op[0]=='text' and op[1]==18 and op[2]==23)
        scale=next((op[3].replace('SCALE: ','').replace(' AT A1','') for op in sheet.ops if op[0]=='text' and op[1]==636 and op[2]==578),'NTS')
        rows.append([f'ADM-HVAC-D-{i:03d}',title,scale])
    rows.extend([['ADM-HVAC-D-018','DRAWING INDEX, DESIGN BASIS AND ISSUE NOTES','NTS'],['ADM-HVAC-D-019','ACTUAL DUCT JUNCTIONS - ENLARGED PLAN DETAILS','AS SHOWN'],['ADM-HVAC-D-020','CROSSING REGISTER / VERTICAL COORDINATION','NTS'],['ADM-HVAC-D-021','REV10 TERMINAL / SIZE CHANGES','NTS']])
    heading(s,18,43,'DETAILED DRAWING INDEX',394)
    table(s,18,52,394,['Drawing number','Drawing title','Scale'],rows,[1.5,4.2,.7],2.5,11.5)
    heading(s,427,43,'REVISION 10 - SCOPE OF ISSUE',394)
    y=57
    for text in ['Routing revision: remove same-service crossovers / duplicate runouts, separate coincident service tracks and render connected exterior walls once.',
                 'Complete tagged fan / heater protection and basement / energy interfaces are added. Existing 85 instrument requirements and room duties are retained. Proposed section size changes and terminal relocations are scheduled on D-021.',
                 'Reference D-113391-ADDC-AES-ME-AC-001_REV.1 is a drafting benchmark; its building duties and instrument requirements are not substituted for this Administration design.']:
        y+=s.para(427,y,text,388,2.8)+8
    heading(s,427,207,'DRAWING / COORDINATION CONVENTIONS',394)
    y=222
    for text in ['All duct sizes: clear internal width x height in mm; D denotes round diameter. Flows: L/s; velocities: m/s. Add approved insulation outside clear sizes.',
                 'Numbered CX tags identify separate-service crossings. Dashed lower edges / continuous upper edges refer to D-020; proposed levels and clearance remain pending.',
                 'MFD* graphic corresponds to conditional FSD-prefixed register tags. Approval of rated boundaries governs quantity, rating and fail positions.',
                 'TT / RHT / DPT room locations are proposed. Pressure references are outdoors. Dashed I&C lines are functional signals, not installed cable routes.']:
        y+=s.para(427,y,text,388,2.8)+8
    heading(s,18,324,'DESIGN BASIS / OPEN ENGINEERING ITEMS',394)
    y=339
    for text in ['Supply 3697.80 L/s; assumed return 3006.68 L/s. Pressure targets +50 Pa normal rooms, +25 Pa kitchen / toilets / clean-agent; actual balance unverified.',
                 'OA reference 420.70 L/s is below 691.12 L/s implied makeup. Toilet net SA-EA is -18.69 L/s; kitchen net is zero. Neither proves the +25 Pa target. Resolve transfer air / extract balance and outdoor-air compliance.',
                 'Fan ESP / curves, fitting K, vertical lengths, levels, support and insulation, diffuser throw / noise, access envelopes and I&C settings remain pending.']:
        y+=s.para(18,y,text,388,2.8)+8
    footer(s,'ISSUE STATUS: FOR ENGINEERING COORDINATION - NOT FOR CONSTRUCTION. Drawn / checked / approved identities and authority are pending. Reference styling does not establish design compliance or professional sign-off.')
    sheets.append(s)

    g['NATIVE_DIM_COUNT']=len(dims)
    g['INSTRUMENTATION_QA']={'scheduled':len(instruments),'unique_graphically_referenced':len(covered),
                            'missing_tags':sorted(set(instruments)-covered),'result':'passed',
                            'index':'Instrument_drawing_index.csv'}
