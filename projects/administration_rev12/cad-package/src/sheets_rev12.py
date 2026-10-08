"""Dimensioned roof proposal, installation details, calculation and I&C sheets."""
import csv,json,math
from shapely.geometry import LineString,box
from shapely.ops import unary_union
from duct_geometry import pieces
from design_rev12 import roof_polygon

def enhance(g):
    Scene,P=g['Scene'],g['P'];sheets=g['SHEETS'];models=g['MODELS']
    frame,heading,table=g['paper_frame'],g['section_heading'],g['table']
    def read(n):
        with (g['BASE']/'schedules'/n).open() as f:return list(csv.DictReader(f))
    report=json.loads((g['OUT']/'engineering_rev12.json').read_text());basis=report['basis']
    routes=read('Roof_routes_Rev12.csv');crosses=read('Roof_crossings_Rev12.csv');risers=read('Roof_risers.csv')
    def notes(s,x,y,title,items,w=385):
        heading(s,x,y,title,w);y+=15
        for t in items:y+=s.para(x,y,t,w,2.8)+7
        return y
    def footer(s,t):g['note_footer'](s,t)
    def page(title,n,scale='NTS'):return frame(title,n,scale=scale)
    def native_dim(scene,a,b,base,angle=0,z=135):
        d=Scene();horizontal=angle==0
        aa=(a[0],base[1]) if horizontal else (base[0],a[1]);bb=(b[0],base[1]) if horizontal else (base[0],b[1])
        d.line([a,aa],'DIM',7);d.line([b,bb],'DIM',7);d.line([aa,bb],'DIM',9)
        for x,y in [aa,bb]:d.line([(x-z*.35,y-z*.35),(x+z*.35,y+z*.35)],'DIM',9)
        ll=abs(b[0]-a[0]) if horizontal else abs(b[1]-a[1])
        d.text((aa[0]+bb[0])/2 if horizontal else base[0]-z*.6,base[1]-z*.6 if horizontal else (aa[1]+bb[1])/2,f'{ll:g}',z,'DIM',align='center',angle=0 if horizontal else 90)
        scene.ops.append(('dimension',a,b,base,angle,z,d.ops));g['NATIVE_DIM_COUNT']+=1
    def roof_model(labels=True,setting=False):
        m=Scene(24500,19500);m.rect(0,0,20000,19500,'ARCH',12)
        for air in ['SA','RA']:
            from shapely.ops import transform
            polys=[transform(lambda x,y:(x,19500-y),roof_polygon(r)) for r in routes if r['air_type']==air]
            exterior=unary_union(polys)
            for edge in pieces(exterior.boundary,'LineString'):m.line(list(edge.coords),air,16)
        for r in routes:
            a,b=[P(*p) for p in json.loads(r['points_mm'])]
            if r['air_type']=='RA':a,b=b,a
            m.arrow((a[0]+.35*(b[0]-a[0]),a[1]+.35*(b[1]-a[1])),(a[0]+.45*(b[0]-a[0]),a[1]+.45*(b[1]-a[1])),'FLOW',10,65)
        # Reserved equipment footprints, with a separate east service strip.
        for c,y in zip('ABC',[9000,12500,16000]):
            m.rect(200,19500-y-2500,1600,2500,'INK',14,None,True)
            m.rect(2000,19500-y-2500,1000,2500,'DIM',9,None,True)
            m.text(*P(1000,y+1300),'PAU-'+c,145,'INK',True,'center')
            m.text(*P(1000,y+900),'RESERVED',110,'NOTE',align='center')
            # Dashed interface stubs are proposed nozzle interfaces, not OEM ports.
            m.line([P(1800,y+1250),P(2300,y+1250)],'SA',12,True)
            m.line([P(1800,y+1750),P(2700,y+1750)],'RA',12,True)
        m.line([P(2300,10250),P(2300,19000)],'SA',10,True)
        m.line([P(2700,10750),P(2700,17750),P(2700,17000)],'RA',10,True)
        m.text(*P(1750,7700),'PAU NOZZLES / BANK MANIFOLDS:',115,'INK',align='center')
        m.text(*P(1750,7300),'OEM CONNECTION DEVELOPMENT PENDING',105,'NOTE',align='center')
        for r in read('Roof_supports_Rev12.csv'):
            rt=next(q for q in routes if q['tag']==r['route']);a,b=json.loads(rt['points_mm']);x,y=float(r['x_mm']),float(r['y_mm']);half=float(rt['width_mm'])/2+65
            ends=[P(x-half,y),P(x+half,y)] if a[0]==b[0] else [P(x,y-half),P(x,y+half)]
            m.line(ends,'DIM',8)
        for rt in routes:
            if rt['role']!='Roof branch':continue
            a,b=json.loads(rt['points_mm']);x,y=(a[0]+b[0])/2,(a[1]+b[1])/2
            if math.dist(a,b)>1800:
                m.text(*P(x-140 if rt['air_type']=='SA' else x+180,y),rt['tag']+' / '+str(int(float(rt['width_mm'])))+'x'+str(int(float(rt['height_mm']))),120,rt['air_type'],angle=90 if a[0]==b[0] else 0,mask=True)
        for r in risers:
            x,y=float(r['x_mm']),float(r['y_mm']);m.circle(*P(x,y),135,r['air_type'],10)
            m.line([P(x-100,y-100),P(x+100,y+100)],r['air_type'],10)
            if labels:
                # Leaders end at reserved tag strips beside each drop.
                dx=-700 if r['air_type']=='SA' or x>18500 else 750
                m.line([P(x,y),P(x+dx,y+450)],'INK',7)
                m.text(*P(x+dx,y+600),r['tag'],125,r['air_type'],align='center',mask=True)
        for r in crosses:
            x,y=float(r['x_mm']),float(r['y_mm']);m.circle(*P(x,y),100,'DIM',7)
            if labels:m.text(*P(x+300,y+240),r['tag'],100,'NOTE',mask=True)
        # Section cuts are proposals referenced to sections D-024.
        m.line([P(7600,17000),P(10400,17000)],'INK',10,True);m.text(*P(7500,17450),'A / D-024',130,'INK',True)
        m.line([P(3600,15600),P(3600,17800)],'INK',10,True);m.text(*P(2700,15700),'B / D-024',130,'INK',True)
        if setting:
            xx=[2300,3600,8200,12500,13400,15500,17000,18100]
            for a,b in zip(xx,xx[1:]):native_dim(m,P(a,19000),P(b,19000),P(0,20500))
            yy=[5000,8250,8450,9800,10400,17000,18150]
            for a,b in zip(yy,yy[1:]):native_dim(m,P(19500,a),P(19500,b),P(21300,0),90)
        return m
    roof=roof_model();models['ROOF_PROPOSAL']=roof
    s=page('ROOF DUCT ROUTING PROPOSAL',23,'1:50')
    g['view'](s,roof,18,50,50,(-500,-500,20500,20000))
    notes(s,465,45,'ROOF ROUTES / LEVELS',["31 connected route segments feed all 15 room supply / return drops. Coordinates use the supplied floor plan origin. Roof footprint and PAU reservation zones must be surveyed.",
        'GREEN SUPPLY: bare BOD +4.800 m; main 600 x 1300 mm. BLUE RETURN: bare BOD +5.550 m; main 700 x 900 mm. Tall roof mains limit plan width; wind / parapet screening and support stability require structural design.',
        '75 mm outdoor insulation each face assumed. Eleven roof plan overlaps have separated insulation envelopes; minimum calculated separation 150 mm. No upper return riser intersects lower supply insulation in this proposed geometry.',
        'PAU-A / B / C reservations: 1600 x 2500 mm each, 1000 mm east service strip. Dashed nozzle stubs and bank manifolds are schematic interfaces awaiting manufacturer dimensions.',
        'RCX tags: Roof_crossings_Rev12 register. A and B sections: D-024. Curbs and supports: D-030. Native centerline setting-out dimensions: D-032.'],350)
    table(s,465,320,350,['Service','Main clear mm','Bare BOD','Insulated top'],[['SA','600 x 1300','+4.800','+6.175'],['RA','700 x 900','+5.550','+6.525']],[.7,1.3,1,1],2.8,16)
    notes(s,465,390,'ACCESS / LOAD HOLD',['Service strips are reserved for PAUs only. Walking platforms, safe roof access, guarding, filter pull-out, common heater / conditional humidifier weather enclosure, banks and lifting path require selected equipment layout. Roof proposal is not an approved installation.'],350)
    footer(s,'Roof levels use provisional roof surface +4.200 m: user underside +4.000 m plus assumed 200 mm slab. Route lengths are measured proposals, not surveyed as-built lengths. All sizes are clear internal mm.');sheets.append(s)

    s=page('ROOF CROSSING AND ROOM DROP SECTIONS',24,'AS SHOWN')
    def zrect(s,x,y,w,zlo,zhi,k,scale=20,zbase=3300):
        top=y-(zhi-zbase)/scale;hh=(zhi-zlo)/scale;s.rect(x,top,w,hh,k,.45)
    for x,title in [(20,'A  RCX-03 / SA08 x RA MAIN  |  1:20'),(427,'B  RS-SA02 DROP  |  VERTICAL 1:20 / HORIZONTAL NTS')]:
        heading(s,x,44,title,390)
        yy=305
        s.line([(x+5,yy),(x+380,yy)],'ARCH',.5);s.text(x+8,yy+8,'MINIMUM CEILING +3.300',2.7,'NOTE')
        zrect(s,x+5,yy,375,4000,4200,'ARCH');s.text(x+245,yy-47,'ROOF +4.200*',2.7,'NOTE');s.text(x+245,yy-35,'SLAB U/S +4.000',2.7,'INK')
        if x==20:
            zrect(s,x+80,yy,30,4800,5200,'SA');zrect(s,x+76.25,yy,37.5,4725,5275,'DIM')
            zrect(s,x+35,yy,150,5550,6450,'RA');zrect(s,x+31.25,yy,157.5,5475,6525,'DIM')
            s.text(x+202,yy-123,'RA BOD +5.550',2.8,'RA');s.text(x+202,yy-75,'SA BOD +4.800',2.8,'SA')
            s.text(x+202,yy-117,'200 BETWEEN INSULATION AT RCX-03',2.6,'INK')
            s.line([(x+145,yy-114),(x+197,yy-114)],'DIM',.25)
            s.text(x+82,yy-196,'SA 600 x 400 / RA 700 x 900',2.7,'DIM')
        else:
            # Open the bottom wall at the connected riser throat.
            s.line([(x+85,yy-75),(x+85,yy-92.5),(x+185,yy-92.5),(x+185,yy-75),(x+115,yy-75)],'SA',.45)
            s.line([(x+85,yy-75),(x+90,yy-75)],'SA',.45)
            zrect(s,x+81.25,yy,107.5,4725,5225,'DIM')
            s.line([(x+90,yy-75),(x+90,yy-13.75),(x+210,yy-13.75)],'SA',.5)
            s.line([(x+115,yy-75),(x+115,yy-5),(x+210,yy-5)],'SA',.5)
            s.rect(x+78,yy-63,50,18,'INK',.3,None,True);s.text(x+202,yy-56,'CURB 300* / WEATHER SEAL',2.7)
            s.text(x+202,yy-71,'ROOF BOD +4.800*',2.7,'SA');s.text(x+202,yy-17,'INDOOR BOD +3.400',2.7,'SA')
            s.text(x+23,yy-102,'TWO ELBOWS / TRANSITION AT ROOF',2.7,'INK')
            s.text(x+23,yy-90,'BARE 500 x 350; RISE 1.400 m*',2.7,'SA')
        s.para(x+5,335,'* Proposed dimensions / levels. Structural slab thickness, beam downstands, curb opening, firestop, weatherproof flashing, pipe / cable routes and support loads require coordination. No roof penetration may be set out from this proposal alone.',375,2.8)
    notes(s,20,412,'VERTICAL DEVELOPMENT / CONNECTION RULES',['Riser straight-length schedules use proposed bare BOD differences at equal-size horizontal ends. Elbow development and differing roof header sizes are separate fitting allowances. Maintain 3.300 m finished ceiling; do not lower a room duct to clear a roof route.',
        'Use shop-developed mitred elbows with turning vanes or selected radiused elbows. Square plan junctions on the roof sheet denote fitted tees; they are not four-way crosses. Every room drop has an independent riser ID and reserved curb opening.'],795)
    footer(s,'Sections are coordination details, 1:20 at A1 where stated; equipment and curb symbols are NTS. Clear opening schedules: Roof_curbs_Rev12. Structural capacity, waterproofing and fire ratings have not been approved.');sheets.append(s)

    s=page('FITTING DEVELOPMENT AND FABRICATION RULES',25)
    for x,title in [(20,'01  MITRED ELBOW / VANES'),(291,'02  THREE-LEG TEE'),(562,'03  NECK / RISER TRANSITION')]:heading(s,x,45,title,258)
    # True open profiles; no line drawn across an open fitting joint.
    s.line([(35,90),(133,90),(133,155)],'SA',.6);s.line([(35,112),(111,112),(111,155)],'SA',.6)
    for a in [116,121,126]:s.line([(a,93),(a-7,105)],'INK',.25)
    s.arrow((45,100),(97,100),'FLOW',.25,2);s.arrow((122,120),(122,148),'FLOW',.25,2)
    s.text(160,105,'W x H: register',2.7);s.text(160,119,'VANES: SHOP DESIGN',2.7);s.text(35,176,'SQUARE THROAT / 45 DEG MITRES',2.7)
    s.line([(308,90),(536,90)],'SA',.6);s.line([(308,112),(401,112),(401,153)],'SA',.6);s.line([(536,112),(429,112),(429,153)],'SA',.6)
    s.arrow((320,100),(510,100),'FLOW',.25,2);s.arrow((415,116),(415,147),'FLOW',.25,2)
    s.text(309,175,'THREE LEGS ONLY; OPEN BRANCH THROAT',2.7)
    s.line([(578,88),(640,88),(695,96),(810,96)],'SA',.6);s.line([(578,125),(640,125),(695,117),(810,117)],'SA',.6)
    s.line([(640,140),(695,140)],'DIM',.25);s.text(667,150,'L >= delta / (2 tan 15 deg)',2.7,align='center')
    s.text(578,174,'MAX 30 DEG INCLUDED ANGLE PROPOSED',2.7)
    notes(s,20,207,'ALL FITTINGS / DIMENSION SCHEDULE',['Fitting_design_Rev12 contains '+str(report['fitting_allowances'])+' tagged loss / geometry allowances covering indoor path bends, joints, terminal adapters, balancing / conditional fire dampers and roof / riser connections. It is a design development register, not an OEM bill of materials.',
        'For an actual two-dimensional reducer, proposed L = max(300 mm, max(abs(W1-W2), abs(H1-H2)) / (2 tan 15 deg)). Hold the bottom level only if the selected terminal / device height permits; otherwise show the offset in the shop section.',
        'Roof main sizes are constant along each service spine, so no unshown step reductions occur. Branch width / height change at the tee is developed within a shop boot. Keep main and branch walls open at the connected throat.',
        'Bend / tee lengths must fit the reserved straight station before moving any VCD, RCD, MFD, EH or access door. Reference CAD glyph dimensions are symbols; actual face-to-face lengths and actuator envelopes require an OEM selection.'],390)
    samples=read('Fitting_design_Rev12.csv');selected=[r for r in samples if r['type']=='Riser elbows (two)']
    table(s,427,207,394,['Fitting','Riser','Clear W x H','Elbows / K each'],[[r['tag'],r['section'],r['clear_w_mm']+' x '+r['clear_h_or_d_mm'],'2 / 0.50 assumed'] for r in selected],[1,1.2,1,1.4],2.6,15)
    heading(s,427,463,'ACTUAL ROOF BRANCH TAPERS - mm',394)
    table(s,427,475,394,['Route','Inlet','Outlet','Developed L'],[[r['tag'],str(r['inlet_width_mm'])+'x'+str(r['inlet_height_mm']),r['width_mm']+'x'+r['height_mm'],r['taper_length_mm']] for r in routes if float(r['taper_length_mm'])],[1.3,1,1,.8],2.6,12)
    footer(s,'All K values on this issue are explicit preliminary allowances, not selected catalogue coefficients. Adapter_details_Rev12 retains the actual connected terminal adaptor coordinates / proposed lengths. Fabrication approval remains open.');sheets.append(s)

    s=page('SYSTEM PRESSURE LOSS AND FAN DUTY BUDGET',26)
    fans=read('Fan_budget_Rev12.csv')
    table(s,20,50,801,['System','Duty each L/s','Estimated external Pa','Budget Pa +20%','Low / high sensitivity Pa'],[[r['system'],f"{float(r['duty_flow_each_l_s']):.2f}",f"{float(r['estimated_external_loss_pa']):.1f}",r['provisional_ESP_with_20_percent_margin_pa'],f"{float(r['low_sensitivity_pa']):.1f} / {float(r['high_sensitivity_pa']):.1f}"] for r in fans],[2.7,1,1.3,1.1,1.7],2.9,25)
    paths=read('Pressure_paths_Rev12.csv');critical=sorted(paths,key=lambda r:float(r['estimated_path_loss_pa']),reverse=True)[:12]
    heading(s,20,180,'CRITICAL TERMINAL PATHS - ALL 52 IN REGISTER',801)
    table(s,20,192,801,['Terminal','Air','Straight Pa','Fittings Pa*','Heater Pa*','Common Pa*','Terminal Pa*','Total Pa*'],[[r['terminal'],r['air_type'],r['straight_loss_pa'],r['assumed_fitting_loss_pa'],r['assumed_heater_loss_pa'],r['assumed_common_external_loss_pa'],r['assumed_terminal_loss_pa'],r['estimated_path_loss_pa']] for r in critical],[1.6,.5,1,1,1,1,1,1],2.7,14)
    notes(s,20,393,'METHOD / BUDGET LIMITS',['Straight friction: Darcy-Weisbach / Colebrook, rho 1.20 kg/m3, mu 1.81e-5 Pa.s, galvanized roughness 0.09 mm, hydraulic diameter 2WH/(W+H). Loss = L x friction + sum(K rho V2/2) + component allowance.',
        'Assumed K: elbows 0.50; tee branch 1.00; tee straight run 0.20; joint bend 0.50; adapter 0.25; balancing damper 2.00; conditional fire damper 1.00. Terminal 30 Pa, room heater 25 Pa, supply common external equipment 150 Pa. Sensitivity scales all assumed local / equipment losses to 50% and 150%.',
        'PAU budget adds worst SA and RA terminal paths. Unit internal coils / dirty filters belong in the OEM fan calculation with explicit external-pressure convention. PAU nozzle / bank manifolds, OA intake, selected dampers, silencers and exhaust discharge are not measured in this model; no fan is selected.'],795)
    footer(s,'Pressure paths include measured proposed roof plan segments and provisional riser rises, plus retained indoor centerlines. Budget values are screening estimates; fan curves, dirty-filter losses and rotating-duty bank cases require OEM confirmation.');sheets.append(s)

    s=page('AIR BALANCE AND TERMINAL SELECTION CRITERIA',27)
    balance=read('Air_balance_Rev12.csv')
    table(s,20,50,801,['GF','Supply L/s','Return L/s','Known extract L/s','Net transfer / leakage L/s','Pressure target / verification'],[[r['room'],f"{float(r['supply_l_s']):.2f}",f"{float(r['return_l_s']):.2f}",f"{float(r['known_extract_l_s']):.2f}",f"{float(r['residual_to_transfer_or_leakage_l_s']):.2f}",r['pressure_target_pa']+' Pa / not verified'] for r in balance],[.5,1,1,1.1,1.6,2],2.8,16)
    notes(s,20,235,'OUTDOOR AIR / PRESSURE ACTION',['Mass-balance minimum OA at the retained SA / RA duty is 691.12 L/s, before any code or process ventilation requirement. Current OA reference 420.70 L/s is short by 270.42 L/s. This is a required design reconciliation, not a selected OA duty.',
        'Known extract is 212.49 L/s; residual exfiltration / transfer is 478.63 L/s less the unresolved clean-agent extract. Verify each door / transfer path and exterior leakage before asserting +50 / +25 Pa.',
        'Toilets have -18.69 L/s net supply minus extract; kitchen has zero net. Positive pressure targets need owner / process / hygiene reconciliation and a measured leakage basis. Do not reduce extract simply to obtain a pressure label.'],390)
    perf=read('Terminal_performance_Rev12.csv');reps=[]
    for room in g['ORDER']:
        r=next(r for r in perf if r['room']==room and r['air_type']=='SA');reps.append([r['tag'],f"{float(r['flow_l_s']):.2f}",r['neck_mm'],r['neck_velocity_m_s'],r['indicative_half_spacing_throw_m']])
    heading(s,427,235,'SUPPLY NECK / COVERAGE SCREEN - 53 ROW REGISTER',394)
    table(s,427,247,394,['Representative','L/s','Neck','m/s','Half spacing m*'],reps,[1.5,.9,.7,.8,1],2.6,15)
    s.para(427,409,'* Half spacing is a coverage screening distance, not certified throw. Require OEM pressure loss, NC and isothermal / cooling throw at 0.25 m/s terminal velocity; check wall coverage, induction, ADPI and occupied-zone draught.',385,2.8)
    s.para(427,453,'Proposed noise brief: NC <=30 meeting / rest / operator rooms; NC <=35 other occupied rooms, subject to owner / acoustic confirmation. No catalogue model, throw or NC has been invented.',385,2.8)
    footer(s,'Duty, neck velocities and same-type spacing are calculated from scheduled terminal coordinates. Air_balance_Rev12 and Terminal_performance_Rev12 are editable calculation / selection registers; existing duties are retained pending engineering reconciliation.');sheets.append(s)

    s=page('INSTRUMENT MOUNTING AND PRESSURE TAP DETAILS',28)
    for x,title in [(20,'A  ROOM STATIC PRESSURE'),(427,'B  FILTER / FAN DIFFERENTIAL')]:heading(s,x,45,title,390)
    s.rect(40,86,220,119,'ARCH',.4);s.text(53,99,'ROOM',3);s.circle(122,133,10,'INST',.3);s.text(122,134,'DPT',2.8,'INST',align='center')
    s.line([(112,133),(75,133),(75,166)],'INST',.3);s.text(53,186,'(+) STATIC TAP',2.8,'INST')
    s.line([(132,133),(278,133),(278,166),(302,166)],'INST',.3);s.text(269,185,'(-) SHELTERED OUTDOOR',2.6,'INST')
    s.text(54,218,'ROOM TT / RHT: +1.500 m AFFL PROPOSED',2.8)
    s.line([(442,112),(800,112)],'SA',.5);s.line([(442,153),(800,153)],'SA',.5);s.rect(605,113,12,39,'INK',.3)
    s.circle(613,79,11,'INST',.3);s.text(613,80,'PDT',2.7,'INST',align='center')
    s.line([(581,133),(581,79),(602,79)],'INST',.3);s.line([(641,133),(641,79),(624,79)],'INST',.3)
    s.text(554,176,'(+) UPSTREAM',2.8,'INST');s.text(675,176,'(-) DOWNSTREAM',2.8,'INST')
    s.arrow((457,133),(530,133),'FLOW',.3,2);s.text(630,216,'PDI: SEPARATE LOCAL GAUGE',2.8,'INST',align='center')
    notes(s,20,256,'INSTALLATION SPECIFICATION - ALL 85 TAGS',['Instrument_installation_Rev12 gives mounting, provisional ranges, pressure connections, wiring, access and commissioning requirements for every instrument. Tag requirement and I/O duties are retained from the approved input register, not replaced with generic symbols.',
        'Proposed room DPT range -100..+100 Pa; fan / filter differential 0..1000 Pa; TT 0..50 degC; RH 0..100%; vibration 0..25 mm/s RMS. Ranges are selection proposals, not final alarm / trip settings.',
        'Use labelled static pressure pickups and equal reference datums. Protect outdoor reference from wind / rain; avoid jet impingement, condensate traps and unserviceable tubing. Provide isolation and test ports per manufacturer.'],390)
    notes(s,427,256,'COMMON-DUCT AIRFLOW / SENSOR ACCESS',['FIT-SA-01 / FIT-RA-01: reserve 5Dh upstream and 3Dh downstream as a screening space allowance. Actual manufacturer measurement station / traversing method governs; no accuracy claim at the provisional roof position.',
        'Main SA Dh = 0.821 m: screen 4.11 m upstream / 2.46 m downstream. Main RA Dh = 0.788 m: screen 3.94 m upstream / 2.36 m downstream. The current short bank-to-first-branch space does not prove these lengths; measurement station integration is an open hold.',
        'Room temperature / humidity sensors avoid direct supply jets, exterior solar gain and heaters. VS installs on approved bearing / frame position. TSHH and AFS remain accessible for test / manual reset; selected heaters govern technology and settings.'],390)
    footer(s,'Installation detail references D-028 / D-029 supplement D-012 to D-016 and the 85-row index. No final cable route, panel terminal number, approved sensor accuracy or OEM setpoint is asserted.');sheets.append(s)

    s=page('I&C WIRING AND HEATER SAFETY INTERFACES',29)
    for x,title in [(20,'A  ANALOG TRANSMITTER / AI'),(427,'B  HARDWIRED HEATER PERMISSIVES')]:heading(s,x,45,title,390)
    for x,y,w,h,t in [(40,91,118,62,'24 VDC / TX'),(265,91,125,62,'HPCP AI'),(444,92,114,65,'AFS CONTACT'),(576,92,114,65,'TSHH LIMIT'),(710,92,97,65,'HEATER\nCONTACTOR')]:
        s.rect(x,y,w,h,'INST',.4);s.text(x+w/2,y+23,t,3,'INST',align='center')
    for yy in [114,135]:s.line([(158,yy),(265,yy)],'INST',.3)
    s.text(209,170,'SHIELDED TWISTED PAIR',2.7,'INST',align='center');s.text(209,185,'4-20 mA PROPOSED / OEM LOOP',2.7,'INST',align='center')
    s.line([(558,125),(576,125)],'INST',.4);s.line([(690,125),(710,125)],'INST',.4)
    s.line([(470,205),(791,205),(791,157)],'INST',.3,True);s.text(468,224,'FIRE TRIP + FAN PROOF + OEM LOCAL SAFETY',2.7,'INST')
    notes(s,20,254,'SIGNAL / PANEL REQUIREMENTS',['AI proposals use isolated 4-20 mA channels and shielded twisted pairs. Confirm transmitter supply, two / three / four wire circuit, loop burden and earthing with OEM. Earth the cable shield at the panel end per project EMC design; segregate from mains / VFD cables.',
        'DI proposals are dry contacts. Contact state, wetting voltage, galvanic isolation and fail-state indication require manufacturer wiring. Local PDI is not an AI. COMM energy meter protocol, CT ratio, address and termination remain pending.',
        'Every tag maps to the unchanged 275-row I/O register. Final channel numbers, junction box locations and cable lengths await panel design and coordinated routes. Commission with traceable point-to-point checks and calibrated simulated signals.'],390)
    notes(s,427,254,'SAFETY / CAUSE AND EFFECT',['Six AFS and six independent TSHH heater provisions remain present. Loss of airflow or high-limit trip inhibits heat through the OEM hardwired circuit. PLC heating demand cannot bypass either permissive. Alarm feedback reports to HPCP.',
        'Confirmed fire stops all HVAC fans and heaters. No automatic fire extraction / purge is added. Fire damper rating, fail position, reset procedure and boundary quantity follow approved fire strategy. Manual reset is required after confirmed fire.',
        'This is an interface diagram, not an electrical terminal drawing. Complete the heater OEM wiring, upstream electrical protection, safety relay architecture and fire interface review before procurement.'],390)
    footer(s,'Input requirement and I/O assignments are retained. Final wiring and approved safety settings require selected hardware. Instrument_installation_Rev12 is the 85-row specification companion.');sheets.append(s)

    s=page('ROOF CURB, SUPPORT AND WEATHERPROOFING',30)
    heading(s,20,44,'A  PROPOSED CURB SECTION - NTS',390)
    s.line([(34,190),(400,190)],'ARCH',.5);s.rect(105,152,136,38,'INK',.5)
    s.line([(118,111),(118,213)],'SA',.5);s.line([(228,111),(228,213)],'SA',.5)
    s.line([(100,152),(100,191),(79,191)],'DIM',.4);s.line([(246,152),(246,191),(267,191)],'DIM',.4)
    s.text(259,155,'300 mm UPSTAND*',2.8);s.text(35,227,'FLASHING / VAPOUR SEAL / FIRESTOP: SELECTED SYSTEM',2.7)
    heading(s,427,44,'B  ADJUSTABLE SUPPORT FRAME - NTS',390)
    s.rect(516,104,184,76,'SA',.45);s.rect(509,97,198,90,'DIM',.3)
    s.line([(489,189),(729,189)],'INK',.65)
    for x in [505,713]:s.line([(x,189),(x,231)],'INK',.65);s.rect(x-19,231,38,9,'INK',.4)
    s.line([(445,244),(802,244)],'ARCH',.4);s.text(468,273,'NONPENETRATING FRAME / LOAD SPREADERS*',2.8)
    notes(s,20,293,'CURBS / PENETRATIONS',['15 curb reservations have X / Y coordinates and opening envelopes: clear duct plus 75 mm insulation and 100 mm installation allowance each side. Upstand 300 mm above proposed roof surface; confirm finished waterproofing datum and local exposure.',
        'Coordinate opening clearances, sleeves, firestop and insulated riser separation with structural and fire disciplines. Keep weatherproofing continuous; selected flashing / vapour seal and cladding joints must shed rain. Do not cut a slab or beam from this drawing.',
        'Outdoor insulation 75 mm is provisional. Specify thermal conductivity, vapour barrier, sealed cladding, weather / UV resistance and fire classification from approved project materials. It is not a declared UAE average.'],390)
    notes(s,427,293,'SUPPORT / ACCESS PROCUREMENT HOLD',[f"{report['roof_support_reservations']} support station reservations, maximum nominal 1500 mm route spacing. Deduplicate junction stations and adjust fitting / equipment supports in shop drawings. Geometry alone does not select a bracket or roof anchor.",
        'Support load table remains TBC until gauge, fitting weight, insulation / cladding, actuator, wind, seismic requirements and frame self-weight are known. Tall roof mains need wind stability / bracing and maintenance platform design.',
        'Verify structure and membrane bearing / protection before choosing nonpenetrating ballast or anchors. PAU lifting, coil / filter withdrawal and heater / humidifier service envelopes require a complete manufacturer footprint.'],390)
    footer(s,'* Proposal only. Roof_curbs_Rev12 and Roof_supports_Rev12 provide setting-out reservations, not anchor design or certified structural loads. Roof surface +4.200 m assumes 200 mm structural slab above the confirmed +4.000 m underside.');sheets.append(s)

    s=page('CEILING COMPONENT AND ACCESS ENVELOPES',31,'AS SHOWN')
    for x,title in [(20,'A  DEEPEST DUCT / FLANGE  |  1:10'),(427,'B  ROOM HEATER / PLENUM  |  NTS')]:heading(s,x,44,title,390)
    # Vertical scaled section includes the flange allowance previously omitted.
    yy=229;s.line([(25,yy),(403,yy)],'ARCH',.5);s.text(28,yy+11,'CEILING +3.300',2.8)
    zrect(s,49,yy,190,4000,4040,'ARCH',10);zrect(s,85,yy,130,3400,3800,'SA',10);zrect(s,80,yy,140,3350,3850,'DIM',10)
    zrect(s,77.5,yy,145,3325,3875,'INK',10)
    s.text(240,yy-69,'SLAB U/S +4.000',2.8);s.text(240,yy-52,'125 mm SLAB ALLOWANCE',2.8)
    s.text(240,yy-32,'25 mm FLANGE EACH SIDE*',2.8);s.text(240,yy-5,'25 mm CEILING GAP',2.8)
    s.rect(456,146,136,50,'SA',.5);s.rect(450,140,148,62,'DIM',.3)
    s.rect(615,125,65,62,'INK',.3,None,True);s.text(626,116,'SIDE ACCESS',2.6)
    s.rect(719,161,70,35,'SA',.4);s.line([(719,196),(789,196)],'FLOW',.5)
    s.text(446,218,'EH CASING + INSULATION <=500 mm OVERALL*',2.8);s.text(700,235,'PLENUM <=350 mm*',2.8)
    notes(s,20,282,'DUCT + FLANGES',['Deepest bare depth 400 mm, BOD +3.400 m, 50 mm insulation each face, proposed 25 mm flange allowance beyond insulation: overall reserved depth 550 mm. Lowest +3.325 m; highest +3.875 m. Ceiling gap reduces to 25 mm; slab allowance reduces to 125 mm.',
        'This is a fit screen, not a maintenance clearance. Hanger / beam / other-service and flange shape / vapour seal require shop coordination. An actuator above the duct can exceed this envelope: select a side actuator / lower-profile assembly or locally reroute.',
        'Installation_envelopes_Rev12 checks every indoor duct and specifies room-heater procurement limits. No selected component envelope is represented as verified.'],390)
    notes(s,427,282,'HEATER / TERMINAL PROCUREMENT LIMITS',['Room heater casing plus insulation must fit between +3.350 and +3.850 m (500 mm overall) unless separately coordinated. Reserve side service access and an aligned ceiling hatch for reset / removal. OEM isolation and thermal clearances govern.',
        'A 350 mm overall terminal plenum above ceiling +3.300 m reaches +3.650 m. Provide an offset / vertical neck to the branch; verify the actual plenum, collar and flex radius in the 700 mm ceiling void. A 600 mm face is not a 600 mm-deep plenum.',
        'All access doors and actuators need a removal path. Final hatch dimensions, heater face-to-face length and damper / actuator position cannot be approved from symbolic plan blocks. If OEM envelopes exceed limits, revise the local branch before release.'],390)
    footer(s,'* Explicit coordination / procurement assumptions, not selected equipment dimensions. A gives a vertical envelope at 1:10 at A1; component illustrations in B are NTS. Minimum clear height remains +3.300 m.');sheets.append(s)

    setting=roof_model(False,True);models['ROOF_SETTING_OUT']=setting
    s=page('ROOF SETTING-OUT AND ROOM DROP REGISTER',32,'1:50')
    g['view'](s,setting,18,49,50,(-500,-500,22500,21400))
    heading(s,498,44,'PROPOSED ROOF DROP COORDINATES - mm',323)
    table(s,498,54,323,['Riser','X','Y','Clear mm','Rise m*'],[[r['tag'],r['x_mm'],r['y_mm'],r['width_mm']+' x '+r['height_mm'],r['vertical_length_m']] for r in risers],[1.4,.8,.8,1.3,.7],2.5,17)
    notes(s,498,339,'SETTING-OUT / REGISTER LINKS',['13 native roof dimension segments supplement the 11 retained architectural dimensions. Individual route end coordinates and lengths are in Roof_routes_Rev12; curbs use the same XY origin.',
        'Local origin is the supplied floor drawing (0,0), not a surveyed benchmark. Verify parapets, equipment plinths, openings, wind screening, beam grids and vertical datums before establishing roof setting-out.',
        '* Rises use provisional roof levels; bend / reducer development and selected PAU nozzle connections are separate. Bank interface stubs are schematic, not dimensioned equipment outlets.'],318)
    footer(s,'Source footprint 20000 x 19500 mm. Dimensions indicate proposed route centerline coordinates. Nominal units mm / m AFFL; proposed heights and fabrication details require professional review and coordinated OEM submissions.');sheets.append(s)

    # Rebuild D-018 from the actual final sheet list to prevent stale references.
    index=page('DRAWING INDEX, DESIGN BASIS AND ISSUE NOTES',18)
    idxrows=[]
    for i,sh in enumerate(sheets,1):
        title=next(op[3].replace('ADMINISTRATION BUILDING - ','') for op in sh.ops if op[0]=='text' and op[1]==18 and op[2]==23)
        scale=next((op[3].replace('SCALE: ','').replace(' AT A1','') for op in sh.ops if op[0]=='text' and op[1]==636 and op[2]==578),'NTS')
        idxrows.append([f'D-{i:03}',title,scale])
    heading(index,18,44,'DRAWING INDEX - REVISION 12',445)
    table(index,18,53,445,['Sheet','Drawing title','Scale'],idxrows,[.8,5.3,.7],2.45,13.5)
    notes(index,480,44,'REV12 ISSUE / BASIS',['Roof routing, sections, fitting development, 52 pressure paths, fan budgets, air balance, all 53 terminal performance criteria, all 85 instrument installation specifications, wiring interfaces, curbs / supports and ceiling component envelopes added.',
        'User basis: +4.000 m structural underside; +3.300 m minimum ceiling. Indoor bare BOD +3.400 m. Roof distribution selected by user; floor-plan roof proposal is not a roof survey.',
        'Preserved: 116 indoor paths; 53 terminal duties / neck / face sizes; 85 instrument requirements and I/O. Indoor duct trees retain zero bare / insulated service crossings.'],338)
    notes(index,480,235,'ASSUMPTIONS / OPEN DESIGN ITEMS',['Roof surface +4.200 m assumes a 200 mm slab. SA bare BOD +4.800 m; RA +5.550 m. Outdoor insulation 75 mm, indoor 50 mm are coordination assumptions.',
        'Pressure losses include explicit preliminary K / equipment allowances and sensitivity. No OEM fan, diffuser, heater or damper has been selected; actual dirty-filter and unit connection losses remain open.',
        'Reconcile OA 420.70 L/s against minimum mass-balance makeup 691.12 L/s, positive room pressure against extract and actual leakage. Final roof survey, structure / waterproofing, wind, fire strategy, wiring and acoustic selections required.'],338)
    footer(index,'ISSUE STATUS: FOR ENGINEERING COORDINATION - NOT FOR CONSTRUCTION. Drawn / checked / approved identities are pending. Native AutoCAD plotting has not been executed in this cloud; review DXF layouts and Save As DWG in AutoCAD.');sheets[17]=index
    g['ENGINEERING_REV12']=report
