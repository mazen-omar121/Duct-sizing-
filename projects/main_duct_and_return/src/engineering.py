"""Seven DX engineering coordination sheets, dimensions and linked schedules."""
from math import ceil, tan, radians
from shapely.geometry import LineString
from shapely.ops import unary_union
from cad import Scene, table


def make_details(c):
    frame, heading, note, footer, sensor = [c[k] for k in ['frame', 'heading', 'note', 'footer', 'sensor']]
    read, write, rooms, dx = [c[k] for k in ['read', 'write', 'rooms', 'dx']]
    details = {}
    connections = []
    for unit in 'ABC':
        for air, flow, hw, hh in [('SA', c['supply']/2, 600, 1300), ('RA', c['return']/2, 700, 900)]:
            length = max(300, ceil(max(abs(700-hw), abs(650-hh))/(2*tan(radians(15)))/25)*25)
            connections.append(dict(tag=f'DX-{air}-{unit}', unit='PAU-'+unit, air_type=air,
                                    flow_l_s=flow, proposed_branch_width_mm=700, proposed_branch_depth_mm=650,
                                    header_width_mm=hw, header_depth_mm=hh, velocity_m_s=round(flow/1000/.455,6),
                                    proposed_taper_length_mm=length, OEM_nozzle_size='TBC', installed_length_and_level='TBC',
                                    detail='MDR-033', status='NEW coordination proposal; nozzle/tee/offset/actual component envelopes and fitting losses require OEM approval'))
    write('DX_bank_connections.csv', connections)

    def taper(s,x,y,a,b,length,scale=10,air='SA'):
        start,end=x,x+length/scale
        s.poly([(start,y-a/scale/2),(end,y-b/scale/2),(end,y+b/scale/2),(start,y+a/scale/2)],air,None,.45)
        s.dimension((start,y+a/scale/2),(end,y+b/scale/2),(start,y+max(a,b)/scale/2+14),scale)
        s.dimension((start,y-a/scale/2),(start,y+a/scale/2),(start-14,y),scale,90)
        s.dimension((end,y-b/scale/2),(end,y+b/scale/2),(end+14,y),scale,90)
        return end

    # Dimensioned coordination spools: actual installed nozzle/port geometry stays open.
    s=frame(33,'DX PAU BRANCH / HEADER TRANSITION DEVELOPMENT','1:10 DETAILS')
    for x,air,a,b,length,depth1,depth2 in [(20,'SA',700,600,1225,650,1300),(434,'RA',700,700,475,650,900)]:
        row=next(r for r in connections if r['air_type']==air)
        length=row['proposed_taper_length_mm']
        heading(s,x,47,air+' / PER DUTY UNIT / COORDINATION PROPOSAL',386)
        s.text(x+8,67,'PLAN - CLEAR WIDTHS',2.8,'INK',True)
        taper(s,x+75,108,a,b,length,air=air)
        s.text(x+8,186,'ELEVATION - CLEAR DEPTHS',2.8,'INK',True)
        taper(s,x+75,260,depth1,depth2,length,air=air)
        s.text(x+8,347,'NOZZLE / FLEX / DAMPER / TEE BODY: OEM DEVELOPMENT',2.7,'PENDING')
    table(s,20,369,800,['Connection','Duty L/s','Branch W x H','Header W x H','m/s','Taper L*'],
          [[r['tag'],f"{r['flow_l_s']:.2f}",'700 x 650',f"{r['header_width_mm']} x {r['header_depth_mm']}",f"{r['velocity_m_s']:.3f}",r['proposed_taper_length_mm']] for r in connections],
          [1.4,1.2,1.4,1.4,1,1],2.7,17)
    footer(s,'* Concentric development L >= max(300, max(delta W,delta H)/(2tan15deg)), rounded up to25 mm. Dimensions are proposed spool development, not selected PAU ports or fabrication release. Three branches; maximum two duty units. Header/branch joining and pressure losses remain OEM/shop coordination.');details[33]=s

    s=frame(34,'ACTUAL ROOF SPLIT / REDUCER / ELBOW DEVELOPMENT','1:10 REDUCER / NTS BOOT')
    heading(s,20,47,'A  R-SA-04A: ACTUAL REGISTERED TAPER',385)
    s.text(28,66,'700 x 450 -> 350 x 400 / L675 / 449.20 L/s',2.9,'SA',True)
    taper(s,95,119,700,350,675)
    taper(s,95,260,450,400,675)
    s.text(28,322,'PLAN ABOVE / ELEVATION BELOW / CLEAR INTERNAL mm',2.65)
    heading(s,434,47,'B  ROOF SPLIT AT X3600 / Y19000',385)
    paths=[([(458,152),(792,152)],30), ([(625,152),(625,277)],35)]
    poly=unary_union([LineString(p).buffer(w/2,cap_style=2,join_style=2) for p,w in paths])
    for edge in [poly.exterior]:s.line(list(edge.coords),'SA',.5)
    s.arrow((480,152),(507,152),'SA');s.arrow((731,152),(763,152),'SA');s.arrow((625,236),(625,264),'SA')
    s.text(475,111,'R-SA-M01 / 3697.80 L/s',2.7,'SA')
    s.text(692,111,'R-SA-M02 / 2583.80 L/s',2.7,'SA')
    s.text(649,253,'R-SA-02-04',2.7,'SA',True);s.text(649,269,'1114.00 L/s',2.7,'SA')
    note(s,440,308,'Open connected throat shown. SA spine600x1300; split branch700x450. Plan boot/radius and depth change are shop proposals. Keep bare BOD+4.800 m; coordinate every insulated offset with MDR-023/024 before release.',369,2.7)
    heading(s,20,372,'ELBOW / TRANSITION / ACCESS DEVELOPMENT',800)
    table(s,20,389,800,['Item','Engineering requirement','Coordination evidence'],[
        ['Reducer','Concentric half-angle <=15deg proposed; actual space and fitted K checked','R-SA-04A taper675 retained; other route tapers in Roof_routes'],
        ['Radius elbow','Proposed centerline radius >= clear width; vanes per selected construction','Actual bend quantities / radii in Fitting_design_Rev12'],
        ['Boot / tee','Keep connected openings; no line across throat; detail all three elevations','Original actual room junction enlargements MDR-019'],
        ['Damper / access','Device body + actuator + removal space; inspection hatch reachable','Components / Device_locations / MDR-028,031'],
        ['Construction','Pressure class, gauge, reinforcement, seam and leakage class to approved spec','OEM/SMACNA-based shop design, project approval pending']],
        [1,3.7,3.3],2.7,21)
    footer(s,'A uses the retained physical route dimensions. B is a development diagram of the registered split, not a new roof route. Actual duct profiles, independent-service separation and riser locations remain as MDR-001/023.');details[34]=s

    s=frame(35,'ROOM DROP / ROOF CURB / FIRESTOP INSTALLATION','VERTICAL 1:20')
    for x,r in [(20,next(r for r in read('Roof_risers.csv') if r['tag']=='RS-SA08')),(434,next(r for r in read('Roof_risers.csv') if r['tag']=='RS-RA08'))]:
        air=r['air_type'];heading(s,x,47,r['tag']+' / TELECOM / '+r['width_mm']+'x'+r['height_mm'],385)
        y0=304
        def zy(z):return y0-(z-3300)/20
        cx=x+139;ww=float(r['width_mm'])/20;roofbod=float(r['roof_bod_mm_affl']);h=float(r['height_mm'])
        s.line([(x+8,zy(3300)),(x+382,zy(3300))],'ARCH',.4)
        s.rect(x+8,zy(4200),374,10,'ARCH',None,.4)
        s.text(x+263,zy(4200)-5,'ROOF +4.200*',2.6,'DIM')
        s.text(x+263,zy(4000)+6,'SLAB U/S+4.000',2.6)
        s.text(x+263,zy(3300)+12,'CEILING +3.300',2.6)
        top=zy(roofbod+h);low=zy(3400)
        s.rect(cx-ww/2,top,ww,low-top,air,None,.45)
        s.rect(cx-ww/2-3.75,top-3.75,ww+7.5,zy(4300)-(top-3.75),'DIM',None,.25)
        s.rect(cx-ww/2-2.5,zy(4000),ww+5,low-zy(4000)+2.5,'DIM',None,.25)
        curb=next(a for a in read('Roof_curbs_Rev12.csv') if a['riser']==r['tag'])
        ow=float(curb['reserved_opening_x_mm'])/20
        s.rect(cx-ow/2,zy(4500),ow,15,'INK',None,.4)
        s.line([(cx-ow/2-10,zy(4200)),(cx-ow/2,zy(4450)),(cx+ow/2,zy(4450)),(cx+ow/2+10,zy(4200))],'INK',.3)
        s.damper(cx,zy(3800),'MFD*',air,motor=True,size=8,fire=True)
        s.text(cx+35,zy(3800),'ACCESS / ACTUATOR / FIRESTOP',2.5,'INST')
        s.line([(cx-ww/2,low),(cx-ww/2-38,low)],air,.45);s.line([(cx+ww/2,low-h/20),(cx+ww/2+38,low-h/20)],air,.45)
        s.dimension((cx-ow/2,zy(4500)),(cx+ow/2,zy(4500)),(cx,zy(4500)-15),20)
        s.dimension((cx+ww/2,zy(roofbod)),(cx+ww/2,zy(3400)),(cx+ww/2+38,zy(3400)),20,90)
        s.text(x+8,350,'CURB OPENING '+curb['reserved_opening_x_mm']+' x '+curb['reserved_opening_y_mm']+' mm*',2.7,'INK',True)
        note(s,x+8,368,'Diagram locates the reserved shaft, curb300 mm upstand, weather flashing and conditional fire damper. Duct cross-section width / level rise are scaled; exact 3D elbow, vertical-transition/roof-to-room insulation joint, sleeve/firestop and selected damper body must be shop-developed.',370,2.7)
        note(s,x+8,442,'For all15 shaft coordinates / openings use MDR-022/032 and the Roof_risers / Roof_curbs tables. Local depth400 with50 mm insulation +25 mm flange allowance leaves25 mm ceiling gap and125 mm slab allowance; actual components/beam access remain open.',370,2.7)
    footer(s,'* Roof+4.200 assumes200 mm slab; outdoor75 / indoor50 mm insulation and curb/opening allowances are proposals. Installed elevations not assigned. RA05 curb extends25 mm beyond nominal footprint: resolve roof/parapet/shaft setting-out before approval.');details[35]=s

    s=frame(36,'COMMON HEADER INSTRUMENTS / CONDENSATE / ACCESS')
    heading(s,20,47,'A  COMMON AIR STATIONS AND SENSORS',800)
    s.duct([(31,107),(801,107)],18,'SA');s.duct([(801,190),(31,190)],18,'RA')
    for x,tag,label,y in [(171,'FIT-SA-01','AF',107),(447,'TT-SA-01','TT',107),(171,'FIT-RA-01','AF',190),(447,'TT-RA-01','TT',190),(675,'RHT-RA-01','RH',190)]:sensor(s,x,y,tag,36,label)
    sensor(s,680,68,'DPT-SA-M01',36,'SP',True);s.line([(680,72.5),(680,107)],'INST',.25)
    s.text(31,80,'ROOF SA HEADER / OUTDOOR ENCLOSURE / STATIC CONTROL OPTIONAL',2.7,'SA',True)
    s.text(31,222,'RA HEADER / AIRFLOW + RETURN TEMPERATURE / HUMIDITY',2.7,'RA',True)
    heading(s,20,259,'B  NEGATIVE-PRESSURE DRAIN-PAN TRAP / SERVICE',385)
    s.rect(32,287,142,45,'INK',None,.35);s.text(103,309,'DX COIL / DRAIN PAN',2.7,'RL',True,'center')
    s.line([(132,332),(132,376),(180,376),(180,345),(283,345)],'INK',.45)
    s.line([(283,345),(298,355),(314,345)],'INK',.35)
    sensor(s,67,354,'LSH-DX-A',36,'LS',True);s.line([(67,349.5),(67,326)],'INST',.25)
    s.text(210,363,'AIR GAP / APPROVED DRAIN',2.6)
    note(s,28,405,'Trap seal / leg dimensions selected from the actual maximum negative pan pressure and OEM instructions; do not select from the provisional fan budget. Prime, provide cleaning access, slope continuous drain, prevent overflow and protect insulation/vapour seals. Apply separately to PAU-A/B/C.',371,2.7)
    heading(s,434,259,'C  MOUNTING / MEASUREMENT / ACCESS RULES',385)
    table(s,434,277,386,['Point','Detailed requirement'],[
        ['FIT','Selected station straight runs / calibration and min-flow check; bank elbows can invalidate station'],
        ['TT/RHT','Serviceable insertion, representative air; no heater radiant bias / condensate contact'],
        ['Static DPT','Flush static pickup, sealed labelled tubing, weather enclosure; station/setpoint OEM review'],
        ['Pressure taps','DPT-SF across fan; filter PDT/PDI tap pairs; identify H/L, isolation/testing access'],
        ['DX refrigerant','Pressure taps / transducers only at approved factory service points'],
        ['Maintenance','Filter pull-out, coil face, trap, compressor, damper and electrical access to OEM drawings']],
        [1,3.6],2.65,35)
    footer(s,'All85 installation specifications are restored in the registers and MDR-028/029. This sheet adds the DX/common-header requirements. LSH example uses PAU-A tag; B/C have the same factory-reviewed function. No trap dimensions or refrigerant service taps are fabricated.');details[36]=s

    causes=[]
    for event,tags,compressor,fan,dampers,reset in [
        ('Confirmed fire / E-stop','FIRE/ESD','Stop all affected DX equipment through approved fire/OEM interface','Stop ALL HVAC fans; heaters OFF','Approved fire positions; not inferred from normal isolation','Manual fire reset after clearance'),
        ('Compressor high pressure','PSH-DX-A|PSH-DX-B|PSH-DX-C','OEM hardwired cutout','OEM safe response; failed unit/changeover as approved','Isolate failed unit if stopped','OEM latch/reset threshold TBC'),
        ('Low pressure','PSL-DX-A|PSL-DX-B|PSL-DX-C','OEM operating-envelope protection','OEM routine; no bypass','OEM safe state','OEM reset / delay TBC'),
        ('Evaporator frost','TSLL-DX-A|TSLL-DX-B|TSLL-DX-C','Inhibit / stage through OEM','OEM defrost/anti-freeze routine','Approved OEM positions','OEM anti-freeze strategy TBC'),
        ('Pan overflow','LSH-DX-A|LSH-DX-B|LSH-DX-C','Proposed inhibit + alarm','OEM safe response','Maintain safe air path','Inspect drain; OEM/manual policy TBC'),
        ('Compressor overload','OL-CMP-DX-A|OL-CMP-DX-B|OL-CMP-DX-C','Local electrical trip','OEM unit fault/changeover','Isolate stopped unit','Local/OEM reset; fault diagnosis'),
        ('DX pressure monitoring','PT-SUC-DX-A|PT-SUC-DX-B|PT-SUC-DX-C|PT-LIQ-DX-A|PT-LIQ-DX-B|PT-LIQ-DX-C','Monitoring only; OEM safeties govern','No new safety bypass','No independent command','OEM alarm thresholds TBC'),
        ('Supply static demand','DPT-SA-M01','OEM cooling/staging logic','Optional fan/VFD control; max TWO duty units','Maintain required room flows','Control range/station/setpoint TBC'),
        ('Fan proof lost','DPT-SF-A|DPT-SF-B|DPT-SF-C','Compressor/heat permissive inhibited via OEM','Stop failed unit; open/prove standby before start','Close stopped unit to avoid reverse flow','Fault clear / approved changeover'),
        ('Filter DP high','PDT-F1-A|PDT-F2-A','Alarm / OEM protection as selected','No arbitrary automatic shutdown','Normal duty unless approved protection','Service filter; threshold OEM'),
        ('Heater airflow/high limit','AFS-EH-COM-01|TSHH-EH-COM-01','DX cooling follows OEM; heater OFF independently','Approved ventilation mode','No safety bypass','Independent heater high-limit reset'),
        ('Standby / rotation','PAU-A|PAU-B|PAU-C','Stopped unit isolated; duty pair selected','Max two running; prove new air path then controlled transfer','Stopped SA/RA/OA closed/proved','Prove normal duty after transfer')]:
        causes.append(dict(event=event,tags=tags,compressor_or_heat=compressor,fan_response=fan,damper_response=dampers,reset=reset,status='Engineering proposal; final OEM/fire controls approval required'))
    write('DX_cause_and_effect.csv',causes)
    s=frame(37,'DX / FAN / DAMPER / FIRE CAUSE AND EFFECT')
    table(s,20,48,800,['Event / references','DX / heating','Fans / maximum duty','Dampers / isolation','Reset'],
          [[r['event']+'\n'+r['tags'].replace('|',' / '),r['compressor_or_heat'],r['fan_response'],r['damper_response'],r['reset']] for r in causes],
          [2.2,2,2,1.6,1.6],2.55,36)
    footer(s,'Proposal for final OEM / fire review. Factory hardwired protections remain local and cannot be bypassed by HPCP. All22 new tags covered in the matrix. Original full-system cause/effect and275 I/O points retained. Fire is not used to initiate extraction/purge.');details[37]=s

    interfaces=[]
    for r in dx:
        category='AI candidate' if r['signal']=='AI proposal' else 'DI candidate' if r['signal']=='DI proposal' else 'OEM LOCAL'
        interfaces.append(dict(tag=r['tag'],category=category,factory_safety='Independent OEM circuit; HPCP cannot bypass',
                               interface='Approved factory data or 4-20mA isolated input' if category=='AI candidate' else 'Approved volt-free contact; contact convention TBC' if category=='DI candidate' else 'Local protection; use approved factory status/communications',
                               panel_channel='UNASSIGNED',detail='MDR-038',status='NEW proposal; verify reuse of existing unit fault/data interface before adding PLC hardware'))
    write('DX_interface_schedule.csv',interfaces)
    s=frame(38,'DX OEM / HPCP FIELD WIRING AND I/O DEVELOPMENT')
    heading(s,20,47,'A  ANALOG LOOP / OEM DATA ALTERNATIVE',385)
    s.rect(30,86,113,49,'INST',None,.35);s.text(86,104,'APPROVED DX TRANSMITTER',2.5,'INST',True,'center');s.text(86,121,'PT-SUC-DX-A EXAMPLE',2.5,'INST',False,'center')
    s.rect(256,86,136,49,'INST',None,.35);s.text(324,104,'ISOLATED PLC AI / HPCP',2.7,'INST',True,'center');s.text(324,121,'CHANNEL / SUPPLY TBC',2.5,'INST',False,'center')
    for y,label in [(94,'LOOP +'),(126,'LOOP -')]:s.line([(143,y),(256,y)],'CTRL',.25,True);s.text(187,y-3,label,2.5,'INST')
    note(s,25,166,'Two-wire illustration only. Sensor supply, isolation and module wiring follow OEM. Route shielded twisted pair apart from motor/VFD power; shield earthing per approved panel design. Factory communication can replace extra transducers if approved.',377,2.65)
    heading(s,434,47,'B  OEM LOCAL SAFETY / APPROVED FAULT INTERFACE',385)
    s.rect(445,86,168,49,'INST',None,.35);s.text(529,107,'HP / LP / FROST / OVERLOAD',2.7,'INST',True,'center');s.text(529,123,'FACTORY SAFETY CHAIN',2.5,'INST',False,'center')
    s.rect(694,86,113,49,'INST',None,.35);s.text(750,105,'OEM CONTROLLER',2.7,'INST',True,'center');s.text(750,122,'FAULT / COMM',2.5,'INST',False,'center')
    s.line([(613,107),(694,107)],'CTRL',.3,True)
    note(s,441,166,'HPCP receives approved status; it does not bridge or modify factory compressor protection. Pan overflow candidate contact convention, fail-safe design and isolation require OEM review. Actual terminals and cable numbers are unassigned.',373,2.65)
    table(s,20,260,800,['New tag','Category','Factory / HPCP interface','Panel assignment'],
          [[r['tag'],r['category'],r['interface'],r['panel_channel']] for r in interfaces],[1.4,1.2,4.2,1.2],2.5,11.2)
    footer(s,'22 candidates =7 AI +3 DI +12 OEM local protections. These are not added silently to the275 baseline I/O rows. Selected factory communications / reused fault contacts can change the final additional count. Wiring is an interface proposal, not a signed terminal schedule.');details[38]=s

    selection=[]
    for unit in 'ABC':
        selection.append(dict(unit='PAU-'+unit,duty='50%; TWO DUTY + ONE ROTATING STANDBY',supply_l_s=c['supply']/2,return_l_s=c['return']/2,
                              minimum_mass_balance_OA_l_s=(c['supply']-c['return'])/2,total_sensible_latent_capacity='TBC - revised room and outdoor-air load',
                              entering_leaving_conditions='TBC',external_static_pressure='TBC - complete route and OEM losses',refrigerant_charge='OEM TBC',
                              footprint_and_nozzles='Reservation only; OEM general arrangement required',detail='MDR-039',status='No DX equipment is selected'))
    write('DX_equipment_schedule.csv',selection)
    s=frame(39,'DX EQUIPMENT SELECTION / ROOM DUTIES / COMMISSIONING')
    table(s,20,48,800,['Unit','Operation','SA L/s','RA L/s','OA lower bound*','DX / fan selection'],
          [[r['unit'],'50% / two duty / one standby',f"{r['supply_l_s']:.2f}",f"{r['return_l_s']:.2f}",f"{r['minimum_mass_balance_OA_l_s']:.2f}",'Capacity, refrigerant, nozzle and ESP TBC'] for r in selection],
          [1,2.2,1,1,1.2,2.7],2.8,27)
    heading(s,20,172,'ROOM AIR DUTIES / MEASURED TAB RECORD REQUIRED',800)
    table(s,20,190,800,['GF / room','SA L/s','RA L/s','EA L/s','Recorded pressure target','Acceptance / unresolved item'],
          [[r['id']+' / '+r['name'],f"{r['sa']:.2f}",f"{r['ra']:.2f}" if r['rn'] else '-',('TBC' if r['id']=='01' else f"{float(r['ea']):.2f}") if r['id'] in ['01','03','09'] else '-',str(int(r['pressure']))+' Pa / unverified','OA / leakage / comfort / field TAB and specified tolerance'] for r in rooms.values()],
          [2.6,1,1,1,1.8,3],2.65,21)
    heading(s,20,414,'PRE-START / COMMISSIONING / PROCUREMENT HOLD',800)
    note(s,20,430,'Confirm roof supports/penetrations/firestops, leakage class/pressure/gauge, weather and vapour seals; inspect fan rotation, duct cleanliness, damper end switches, drain/trap prime and every instrument scale. Prove fire stop and independent heater/DX safeties. Balance all53 terminals; record each room SA/RA/EA and pressure with sheltered outdoor reference. Confirm comfort/humidity against revised thermal loads.',797,2.7)
    note(s,20,476,'* Total makeup lower bound691.12 L/s exceeds earlier OA420.70 by270.42. Unknown CAG extract remains open; toilet net-18.69 and kitchen0 do not establish+25 Pa. The52 Rev12 pressure paths are preliminary allowances excluding bank/nozzle/OA details; they do not select a DX fan. Complete OEM coils/dirty filters, actual accessories and full fan curve before procurement.',797,2.7)
    footer(s,'No capacities, refrigerant safety settings, airflow tolerances, leakage measurements or certified diffuser throw/NC are invented. All room duties / necks / faces remain in the full retained registers. Installed levels and final engineering approval remain open.');details[39]=s
    return details
