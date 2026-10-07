"""One-time Rev10 -> Rev11 roof-distribution proposal; not a normal build step."""
import csv, json, math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'projects/administration_rev10/cad-package'
NEW=ROOT/'projects/administration_rev11/cad-package'
def read(name):
    with (OLD/'schedules'/name).open() as f:return list(csv.DictReader(f))
def write(name,rows,fields=None):
    with (NEW/'schedules'/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    original=read('Duct_sections.csv');old={r['tag']:r.copy() for r in original}
    rows=[r.copy() for r in original if r['role']!='Main'];by={r['tag']:r for r in rows}
    def route(tag,points,wh=None,q=None):
        r=by[tag];r['points_mm']=json.dumps(points)
        if wh:r['width_mm'],r['height_mm']=map(str,wh)
        if q is not None:r['flow_l_s']=str(round(q,6))
    def add(tag,template,points,q,wh):
        r=by[template].copy();r.update(tag=tag,role='Room header');rows.append(r);by[tag]=r;route(tag,points,wh,q)
    # Short independent room connections replace all indoor common-main feeders.
    for tag,pp in {
        'SA-B02':[[3600,16600],[4800,16600]],
        'SA-B05':[[12500,12800],[14000,12800],[14000,13200]],
        'SA-B04':[[4200,6500],[2900,6500]],
        'SA-B08':[[9800,5600],[8500,5600]],
        'SA-B06':[[12500,9475],[12500,10700]],
        'SA-B07':[[15500,5000],[15500,3600],[14100,3600]],
        'SA-B09':[[13400,8200],[13400,7600]],
        'SA-B03':[[17000,7000],[18200,7000]],
        'SA-B01':[[19400,3500],[16800,3500]],
        'RA-B04':[[4800,7300],[4800,8250]],
        'RA-B05':[[19500,11400],[19500,10400]],
        'RA-B06':[[11300,8850],[11300,9800]],
        'RA-B07':[[13000,2200],[13000,5000]],
    }.items():route(tag,pp)
    route('SA-H03-D01',[[18200,7000],[18200,6600]])
    # Panel room return runs around the supply tree, with a northern merge.
    q=float(by['RA-B02']['flow_l_s'])/4
    route('RA-B02',[[6000,19100],[6000,18150]],(650,400))
    route('SA-H02-U01',[[4800,16600],[4800,17700]])
    route('SA-R02-01',[[4800,17700],[2700,17700]])
    route('SA-R02-02',[[4800,17700],[7100,17700]])
    route('RA-H02-U01',[[1500,17000],[1500,19100]],(450,350),2*q)
    route('RA-H02-D01',[[1500,11900],[1500,17000]],(450,350),q)
    add('RA-H02-E01','RA-H02-U01',[[8050,11900],[8050,17000]],q,(450,350))
    add('RA-H02-E02','RA-H02-U01',[[8050,17000],[8050,19100]],2*q,(450,350))
    add('RA-H02-N01','RA-H02-U01',[[1500,19100],[6000,19100]],2*q,(450,350))
    add('RA-H02-N02','RA-H02-U01',[[8050,19100],[6000,19100]],2*q,(450,350))
    for j,x,y,rail in [(1,2000,17000,1500),(2,7700,17000,8050),(3,2000,11900,1500),(4,7700,11900,8050)]:
        route(f'RA-R02-{j:02d}',[[x,y],[rail,y]])
    # Telecom return likewise stays on the perimeter; no grille cross-bars.
    q=float(by['RA-B08']['flow_l_s'])/6
    route('RA-B08',[[9400,7500],[9400,8450]],(850,400))
    route('RA-H08-D02',[[5800,900],[5800,4600]],(500,350),q)
    route('RA-H08-D01',[[5800,4600],[5800,7150]],(500,350),2*q)
    route('RA-H08-U01',[[5800,7150],[5800,7500]],(500,350),3*q)
    add('RA-H08-E01','RA-H08-D02',[[11500,900],[11500,4600]],q,(500,350))
    add('RA-H08-E02','RA-H08-D02',[[11500,4600],[11500,7150]],2*q,(500,350))
    add('RA-H08-E03','RA-H08-D02',[[11500,7150],[11500,7500]],3*q,(500,350))
    add('RA-H08-N01','RA-H08-U01',[[5800,7500],[9400,7500]],3*q,(500,350))
    add('RA-H08-N02','RA-H08-U01',[[11500,7500],[9400,7500]],3*q,(500,350))
    for j,x,y,rail in [(1,5500,7150,5800),(2,11500,7150,11500),(3,5500,4600,5800),(4,11500,4600,11500),(5,5500,900,5800),(6,11500,900,11500)]:
        # Integral right-hand necks are shown with a small plan offset.
        xx=11400 if x==11500 else x
        route(f'RA-R08-{j:02d}',[[xx,y],[rail,y]])
    for j,y in [(1,6500),(3,4200),(5,1700)]:route(f'SA-R08-{j:02d}',[[8500,y],[6800,y]])
    # Wider, shallower operator and corridor return sections preserve area.
    for r in rows:
        h=float(r['height_mm']) if r['height_mm'] else 0
        if h>400:
            w=math.ceil(float(r['width_mm'])*h/400/50)*50
            r['width_mm'],r['height_mm']=str(w),'400'
        r.update(zone='INDOOR',proposed_bod_mm_affl='3400',level_status='Proposed bare BOD; OEM flanges / terminal plenums / beams / access pending')
        r['level']='Bare BOD +3.400 m proposed'
        pp=json.loads(r['points_mm']);r['horizontal_length_m']=str(round(sum(math.dist(a,b) for a,b in zip(pp,pp[1:]))/1000,4))
        w=float(r['width_mm'])/1000;h=float(r['height_mm'])/1000 if r['height_mm'] else None
        area=w*h if h else math.pi*w*w/4;v=float(r['flow_l_s'])/1000/area;dh=2*w*h/(w+h) if h else w
        ff=.02;re=1.2*v*dh/1.81e-5
        for _ in range(20):ff=1/(-2*math.log10(.00009/(3.7*dh)+2.51/(re*math.sqrt(ff))))**2
        r['velocity_m_s']=str(round(v,5));r['friction_pa_m']=str(round(ff/dh*1.2*v*v/2,5))
        r['route_basis']='Rev11 roof-main option, independent room riser; geometry and local envelope proposal, actual roof routing / structural penetrations / ESP / OEM selection pending'
    terms=read('Terminals.csv');moves={
        'SD-02-01':(2700,17700),'SD-02-02':(7100,17700),
        'RG-02-01':(2000,17000),'RG-02-03':(2000,11900),
        'RG-08-01':(5500,7150),'RG-08-03':(5500,4600),'RG-08-05':(5500,900),
        'RG-08-02':(11400,7150),'RG-08-04':(11400,4600),'RG-08-06':(11400,900),
        'SD-08-01':(6800,6500),'SD-08-03':(6800,4200),'SD-08-05':(6800,1700)}
    changes=[]
    for r in terms:
        if r['tag'] in moves:
            x,y=moves[r['tag']];changes.append(dict(tag=r['tag'],old_x_mm=r['x_mm'],old_y_mm=r['y_mm'],new_x_mm=str(x),new_y_mm=str(y),flow_l_s=r['flow_l_s'],status='Proposed; reflected ceiling / throw / noise and access coordination pending'))
            r['x_mm'],r['y_mm']=str(x),str(y)
    write('Terminals.csv',terms);write('Rev11_terminal_changes.csv',changes)
    components=read('Components.csv')
    for r in components:
        if r['tag']=='EH-COM-01':
            r['service']='Common electric duct heater in proposed weather-protected roof enclosure'
            r['selection_status']='Rev11 roof option; OEM weather suitability / enclosure / safety / duty TBC'
        if r['tag'] in ['HUM-01','AD-HCOM-01']:
            r['selection_status']='Rev11 proposed weather-protected roof plant; conditional duty / mounting / maintenance access TBC'
    write('Components.csv',components)
    write('Duct_sections.csv',rows)
    roof=[dict(tag=r['tag'],air_type=r['air_type'],width_mm=r['width_mm'],height_mm=r['height_mm'],flow_l_s=r['flow_l_s'],velocity_m_s=r['velocity_m_s'],zone='ROOF_PROPOSAL',status='Functional flow/size basis only; actual roof route, lengths, levels, weather insulation and fitting losses TBC') for r in original if r['role']=='Main']
    write('Roof_main_basis.csv',roof)
    risers=[]
    for r in rows:
        if r['role']!='Branch':continue
        pp=json.loads(r['points_mm']);x,y=pp[0 if r['air_type']=='SA' else -1]
        risers.append(dict(tag='RS-'+r['air_type']+r['room'],branch=r['tag'],air_type=r['air_type'],room=r['room'],x_mm=x,y_mm=y,width_mm=r['width_mm'],height_mm=r['height_mm'],flow_l_s=r['flow_l_s'],indoor_bod_mm_affl=3400,roof_bod_mm_affl='TBC',vertical_length_m='TBC',status='Proposed roof penetration/drop; structural approval, curb, weatherproofing, fire rating and access pending'))
    write('Roof_risers.csv',risers)
    depth=[]
    for r in rows:
        h=float(r['height_mm'] or r['diameter_mm']);depth.append(dict(section=r['tag'],air=r['air_type'],room=r['room'],bare_depth_mm=h,bare_bod_mm_affl=3400,insulation_mm=50,lowest_insulated_mm_affl=3350,highest_insulated_mm_affl=3450+h,slab_clearance_mm=550-h,finished_ceiling_mm_affl=3300,ceiling_clearance_mm=50,status='Duct envelope fits only; actual support, flange, actuator and terminal/plenum envelope unverified'))
    write('Headroom_register.csv',depth)
    routes=[dict(tag=r['tag'],previous_points_mm=old[r['tag']]['points_mm'] if r['tag'] in old else 'NEW',revised_points_mm=r['points_mm'],status='Indoor roof-drop proposal') for r in rows if r['tag'] not in old or r['points_mm']!=old[r['tag']]['points_mm']]
    write('Rev11_route_changes.csv',routes)
    resized=[dict(tag=r['tag'],previous_size_mm=old[r['tag']]['width_mm']+'x'+old[r['tag']]['height_mm'],revised_size_mm=r['width_mm']+'x'+r['height_mm'],flow_l_s=r['flow_l_s'],velocity_m_s=r['velocity_m_s']) for r in rows if r['tag'] in old and (r['width_mm'],r['height_mm'])!=(old[r['tag']]['width_mm'],old[r['tag']]['height_mm'])]
    write('Rev11_size_changes.csv',resized)
    basis=json.loads((OLD/'inputs/Coordination_basis.json').read_text())
    basis.update(finished_ceiling_mm_affl=3300,minimum_clear_headroom_mm=3300,ceiling_datum_source='User requires 3.3 m below 4.0 m slab/roof underside',proposed_indoor_bod_mm_affl=3400,installed_duct_bod_mm_affl=None,structure_to_insulation_allowance_mm=150,ceiling_to_insulation_allowance_mm=50,distribution_strategy='Roof common mains with 15 independent room supply/return drops - proposed option, user selection pending',calculation_status='Connected indoor trees at proposed bare BOD +3.400 m; single-layer envelope only, not installation approval; roof distribution NTS / survey and structural coordination pending')
    (NEW/'inputs/Coordination_basis.json').write_text(json.dumps(basis,indent=2)+'\n')
    print(len(rows),'indoor paths;',len(risers),'proposed risers;',len(resized),'size changes;',len(changes),'terminal moves')

if __name__=='__main__':main()
