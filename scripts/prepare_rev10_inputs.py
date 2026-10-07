"""Create the documented Rev10 routing proposal from the published Rev09 inputs.

This is a revision migration, not part of a normal drawing rebuild. Running it
again replaces Rev10 routing inputs; do not use it after editing those inputs.
"""
from pathlib import Path
import csv
import json
import math

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'projects/administration_rev09/cad-package/schedules'
NEW = ROOT / 'projects/administration_rev10/cad-package/schedules'


def read(name):
    with (OLD / name).open() as f:
        return list(csv.DictReader(f))


def write(name, rows):
    with (NEW / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    rows = read('Duct_sections.csv')
    bytag = {r['tag']: r for r in rows}
    changes = []

    def route(tag, points, reason, flow=None, wh=None):
        r = bytag[tag]
        old = r.copy()
        r['points_mm'] = json.dumps(points)
        if flow is not None:
            r['flow_l_s'] = str(round(flow, 6))
        if wh:
            r['width_mm'], r['height_mm'] = map(str, wh)
        r['horizontal_length_m'] = str(round(sum(math.dist(a, b) for a, b in zip(points, points[1:])) / 1000, 4))
        w = float(r['width_mm']) / 1000
        h = float(r['height_mm']) / 1000 if r['height_mm'] else None
        area = w * h if h else math.pi * w * w / 4
        v = float(r['flow_l_s']) / 1000 / area
        r['velocity_m_s'] = str(round(v, 5))
        # Imported Colebrook convention: 90 micrometre roughness, rho=1.2,
        # dynamic viscosity=1.81e-5 Pa.s. This is not a fan ESP calculation.
        dh = 2 * w * h / (w + h) if h else w
        re = 1.2 * v * dh / 1.81e-5
        ff = .02
        for _ in range(20):
            ff = 1 / (-2 * math.log10(.00009/(3.7*dh) + 2.51/(re*math.sqrt(ff))))**2
        r['friction_pa_m'] = str(round(ff / dh * 1.2 * v * v / 2, 5))
        r['route_basis'] = 'Rev10 proposed routing: ' + reason + '; BOD / insulation / selected fitting losses and OEM clearance TBC'
        changes.append({'tag': tag, 'previous_points_mm': old['points_mm'], 'revised_points_mm': r['points_mm'],
                        'previous_size_mm': old['width_mm'] + 'x' + old['height_mm'],
                        'revised_size_mm': r['width_mm'] + 'x' + r['height_mm'],
                        'previous_flow_l_s': old['flow_l_s'], 'revised_flow_l_s': r['flow_l_s'],
                        'reason': reason, 'status': 'Proposed coordination revision; approval / levels pending'})

    def add(tag, template, points, flow, reason, wh=None):
        r = bytag[template].copy()
        r['tag'] = tag
        r['role'] = 'Room header'
        rows.append(r)
        bytag[tag] = r
        route(tag, points, reason, flow, wh)
        changes[-1]['previous_points_mm'] = 'NEW'
        changes[-1]['previous_size_mm'] = 'NEW'
        changes[-1]['previous_flow_l_s'] = ''

    sy, ry = 9475, 8225
    route('SA-M02', [[1800,16600],[1800,12525]], 'Operator take-off below the GF-02 supply terminal row')
    route('SA-M03', [[1800,12525],[1800,sy],[4150,sy]], 'Corridor supply track; narrower plan width', wh=(650,750))
    route('SA-M04', [[4150,sy],[5700,sy]], 'Corridor supply track; narrower plan width', wh=(650,575))
    route('SA-M05', [[5700,sy],[12500,sy]], 'Common corridor branch take-off at x=12500')
    route('SA-M06', [[12500,sy],[13400,sy]], 'Continue after corridor take-off')
    for tag,a,b in [('SA-M07',13400,15500),('SA-M08',15500,17800),('SA-M09',17800,19400)]:
        route(tag, [[a,sy],[b,sy]], 'Corridor supply track / clear eastern clean-agent branch')
    route('RA-M01', [[3500,15500],[3500,19000]], 'GF-02 return take-off separated from supply branch')
    route('RA-M02', [[3500,11400],[3500,15500]], 'Operator return below all GF-02 return runouts')
    route('RA-M03', [[4800,ry],[3500,ry],[3500,11400]], 'Corridor return track; narrower plan width', wh=(600,800))
    route('RA-M04', [[8000,ry],[4800,ry]], 'Corridor return track; meeting return at x=4800', wh=(600,600))
    route('RA-M05', [[11300,ry],[8000,ry]], 'Corridor return track; preserve section area with deeper, narrower duct', wh=(350,575))
    route('RA-M06', [[13000,ry],[11300,ry]], 'Bed-room return track clear of supply / toilet header', wh=(350,300))

    route('SA-B05', [[1800,12525],[14000,12525],[14000,13200]], 'Separate feeder from the GF-02 bottom supply runouts')
    route('RA-B02', [[6000,15500],[3500,15500]], 'Separate the room return branch from the supply branch')
    route('RA-H02-U01', [[6000,17000],[6000,15500]], 'Return header above revised branch')
    route('RA-H02-D01', [[6000,11900],[6000,15500]], 'Return header below revised branch')
    for j,x,y in [(1,5400,17000),(2,7700,17000),(3,5400,11900),(4,7700,11900)]:
        route(f'RA-R02-{j:02d}', [[x,y],[6000,y]], 'Individual return neck; no crossing of the common return main')

    # Meeting room: two independent, spaced headers.
    route('SA-B04', [[4150,sy],[4150,6500],[2900,6500]], 'Meeting supply track between the common return main and room return header', wh=(350,400))
    route('SA-R04-02', [[2900,4300],[4100,4300]], 'Clear the return header and leave space at the diffuser face')
    route('RA-B04', [[4800,7300],[4800,ry]], 'Straight meeting return branch after the highest grille')
    for tag,points in [('RA-H04-U01',[[4800,7200],[4800,7300]]),
                       ('RA-H04-D01',[[4800,4300],[4800,7200]]),
                       ('RA-H04-D02',[[4800,1000],[4800,4300]])]:
        route(tag, points, 'Return header spaced from the meeting supply header')
    # Recalculate the changed full-flow upper segment using the same helper.
    route('RA-H04-U01', [[4800,7200],[4800,7300]], 'Common return segment after all three grilles', flow=float(bytag['RA-B04']['flow_l_s']))
    for j,x,y in [(1,700,7200),(2,5000,4300),(3,700,1000)]:
        route(f'RA-R04-{j:02d}', [[x,y],[4800,y]], 'Individual return neck / integral short neck where noted')

    # Telecom: supply feeder ends above its first outlet row; return at east edge.
    route('SA-B08', [[5700,sy],[5700,5600],[8500,5600]], 'Feeder west of every supply runout')
    route('SA-H08-U01', [[8500,5600],[8500,6500]], 'Upper outlet pair above the feeder', flow=294.866667)
    route('SA-H08-D01', [[8500,5600],[8500,4200]], 'Lower outlet pairs below the feeder')
    route('RA-B08', [[11250,7650],[8000,7650],[8000,ry]], 'Return branch clear of supply header and return main', wh=(500,650))
    route('RA-H08-U01', [[11250,7150],[11250,7650]], 'Common return header after the upper pair', flow=825.26339, wh=(500,650))
    route('RA-H08-D01', [[11250,4600],[11250,7150]], 'Return collection rail clear of supply runouts', wh=(500,650))
    route('RA-H08-D02', [[11250,900],[11250,4600]], 'Return collection rail clear of supply runouts', wh=(500,650))
    for j,x,y in [(1,6400,7150),(2,11500,7150),(3,5900,4600),(4,11500,4600),(5,5900,900),(6,11500,900)]:
        route(f'RA-R08-{j:02d}', [[x,y],[11250,y]], 'Separate left / right necks; right neck uses integral plenum drop')

    # Operator room: a perimeter return tree, not cross-bars through supply.
    q = 718.3633896036071 / 5
    route('RA-B05', [[19500,11400],[3500,11400]], 'Common return feeder below the room supply tree', wh=(500,525))
    route('RA-H05-U01', [[19500,12500],[19500,11400]], 'East return rail after right middle grille', flow=4*q, wh=(500,525))
    route('RA-H05-U02', [[19500,18800],[19500,12500]], 'East return rail after the upper right grille', flow=3*q, wh=(500,525))
    route('RA-H05-U03', [[19500,19000],[19500,18800]], 'East return rail before the upper right grille', flow=2*q, wh=(500,525))
    route('RA-H05-D01', [[9600,14600],[9600,18800]], 'West return rail; no crossing of supply header', flow=q, wh=(500,525))
    add('RA-H05-L01','RA-H05-D01',[[9600,18800],[9600,19000]],2*q,'West return rail after both left grilles')
    add('RA-H05-N01','RA-H05-D01',[[9600,19000],[19500,19000]],2*q,'Return bridge north of all supply outlets')
    for j,x,y,xx,yy in [(1,9900,18800,9600,18800),(2,19000,18800,19500,18800),
                        (3,9900,14600,9600,14600),(4,19000,12500,19500,12500),
                        (5,15100,12000,19500,12000)]:
        route(f'RA-R05-{j:02d}', [[x,y],[xx,yy]], 'Individual return neck to the perimeter rail')
    # The fifth outlet joins the east rail as a side tee above the feeder.
    route('RA-H05-U01', [[19500,12500],[19500,12000]], 'East rail before the fifth outlet', flow=4*q, wh=(500,525))
    add('RA-H05-E01','RA-H05-U01',[[19500,12000],[19500,11400]],5*q,'East rail after the fifth outlet')

    # Corridor: real shared collection / distribution, with aggregate header flows.
    sq, rq = 418.2/3, 358.863389603607/4
    route('SA-B06', [[12500,sy],[12500,10700]], 'Straight common branch before the three-way distribution / heater station')
    route('SA-H06-D01', [[12500,10700],[5400,10700]], 'West supply header; one outlet', flow=sq)
    add('SA-H06-E01','SA-H06-D01',[[12500,10700],[14700,10700]],2*sq,'East supply header; two outlets')
    add('SA-H06-E02','SA-H06-D01',[[14700,10700],[18300,10700]],sq,'East supply header after second outlet')
    for j,x in [(1,5400),(2,14700),(3,18300)]:
        route(f'SA-R06-{j:02d}', [[x,10700],[x,10150]], 'Single neck to a corridor outlet; no backtracking over its feeder')
    route('RA-B06', [[11300,8850],[11300,ry]], 'Straight common corridor collection branch', wh=(350,550))
    route('RA-H06-D01', [[17200,8850],[11300,8850]], 'East return collection header; two grilles', flow=2*rq, wh=(350,550))
    add('RA-H06-L01','RA-H06-D01',[[4500,8850],[9700,8850]],rq,'West collection header; one grille')
    add('RA-H06-L02','RA-H06-D01',[[9700,8850],[11300,8850]],2*rq,'West collection header; two grilles')
    add('RA-H06-E01','RA-H06-D01',[[18300,8850],[17200,8850]],rq,'East collection header before third grille')
    for j,x in [(1,4500),(2,9700),(3,17200),(4,18300)]:
        route(f'RA-R06-{j:02d}', [[x,8875],[x,8850]], 'Individual integral neck; common runs are rectangular headers, not duplicated round runouts')

    route('SA-B09', [[13400,sy],[13400,7600]], 'Toilet supply header clear of bed-room return rail')
    route('SA-H09-D01', [[13400,7600],[13400,7000]], 'Separate toilet supply header')
    route('SA-H09-D02', [[13400,7000],[13400,5200]], 'Separate toilet supply header')
    for j,y in [(1,7000),(2,5200)]:
        route(f'SA-R09-{j:02d}', [[13400,y],[13600,y]], 'Short integral neck to toilet diffuser')
    route('SA-B07', [[15500,sy],[15500,3600],[14100,3600]], 'Bed-room supply branch clear of its return branch')
    route('RA-B07', [[13000,2200],[13000,ry]], 'West bed-room return branch; no coincident supply / return run')
    route('RA-H07-D01', [[13000,1400],[13000,2200]], 'West bed-room return rail')
    route('RA-R07-01', [[14400,1400],[13000,1400]], 'Return neck to the west rail')
    route('SA-B03', [[17800,sy],[17800,7300],[18200,7300]], 'Kitchen supply branch')
    route('SA-B01', [[19400,sy],[19400,3500],[16800,3500]], 'Eastern clean-agent feed; avoids crossing the kitchen supply branch')
    route('SA-H01-D01', [[16800,3500],[16800,3000]], 'Straight outlet station clear of the clean-agent feeder elbow')
    route('SA-R01-01', [[16800,3000],[18100,3000]], 'Terminal neck clear of the common feeder')

    terminals = read('Terminals.csv')
    moves = {'RG-02-01':(5400,17000),'RG-02-03':(5400,11900),
             'SD-04-02':(4100,4300),'RG-04-01':(700,7200),'RG-04-02':(5000,4300),
             'RG-05-01':(9900,18800),'RG-05-03':(9900,14600),'RG-05-05':(15100,12000),
             'RG-08-01':(6400,7150),'RG-08-02':(11500,7150),'RG-08-04':(11500,4600),'RG-08-06':(11500,900),
             'SD-06-01':(5400,10150),'SD-06-02':(14700,10150),'SD-06-03':(18300,10150),
             'RG-06-01':(4500,8875),'RG-06-02':(9700,8875),'RG-06-03':(17200,8875),'RG-06-04':(18300,8875),
             'SD-09-01':(13600,7000),'SD-09-02':(13600,5200),'SD-01-01':(18100,3000)}
    terminal_changes=[]
    for t in terminals:
        if t['tag'] in moves:
            x,y=moves[t['tag']]
            terminal_changes.append({'tag':t['tag'],'old_x_mm':t['x_mm'],'old_y_mm':t['y_mm'],
                                     'new_x_mm':x,'new_y_mm':y,'flow_l_s':t['flow_l_s'],
                                     'reason':'Proposed relocation for separated routing / corridor service',
                                     'status':'Coordinate ceiling layout and diffuser / grille performance before approval'})
            t['x_mm'],t['y_mm']=str(x),str(y)
    write('Duct_sections.csv', rows)
    write('Terminals.csv', terminals)
    write('Rev10_route_changes.csv', changes)
    write('Rev10_terminal_changes.csv', terminal_changes)
    baseline={r['tag']:r for r in read('Duct_sections.csv')}
    size_changes=[]
    for r in rows:
        old=baseline.get(r['tag'])
        if old and (old['width_mm'],old['height_mm'])!=(r['width_mm'],r['height_mm']):
            size_changes.append({'tag':r['tag'],'previous_size_mm':old['width_mm']+'x'+old['height_mm'],
                                 'revised_size_mm':r['width_mm']+'x'+r['height_mm'],'flow_l_s':r['flow_l_s'],
                                 'velocity_m_s':r['velocity_m_s'],'status':'Proposed clear size; coordinate levels and selected fitting loss / fan ESP'})
    write('Rev10_size_changes.csv',size_changes)
    print(f'Rev10 inputs: {len(rows)} sections, {len(changes)} routing entries, {len(terminal_changes)} proposed terminal relocations')


if __name__ == '__main__':
    main()
