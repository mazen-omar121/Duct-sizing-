"""Rev08 corrections from the three supplied 06-Oct connection close-ups."""
from pathlib import Path
from math import hypot
import csv,json
BASE=Path(__file__).resolve().parents[1]
def read(name):return list(csv.DictReader((BASE/'schedules'/name).open()))
def write(name,rows):
 with (BASE/'schedules'/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

# The old GF-02 return branch doubled back along its own collection header.
# Separate its departure from the header and its straight damper station.
routes={
 'RA-B02':[(6000,16400),(3500,16400)],
 'RA-H02-U01':[(6000,17000),(6000,16400)],
 'RA-H02-D01':[(6000,11900),(6000,16400)],
 'RA-R02-01':[(1200,17000),(6000,17000)],
 'RA-R02-02':[(7700,17000),(6000,17000)],
 'RA-R02-03':[(1200,11900),(6000,11900)],
 'RA-R02-04':[(7700,11900),(6000,11900)],
}
rows=read('Duct_sections.csv')
for r in rows:
 if r['tag'] in routes:
  p=routes[r['tag']];r['points_mm']=json.dumps(p)
  r['horizontal_length_m']=str(round(sum(hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(p,p[1:]))/1000,3))
  r['route_basis']='Rev08 proposed GF-02 return clearance route; branch no longer coincides with its collection header. Duct levels / fabrication development TBC'
write('Duct_sections.csv',rows)
terminals=read('Terminals.csv')
for r in terminals:
 if r['tag'] in ['RG-02-01','RG-02-02']:r['y_mm']='17000'
write('Terminals.csv',terminals)

corrections=[
 {'comment':'Missing outside walls at connected duct joints','correction':'Use the exterior of locally joined section polygons; preserve shared external walls and remove only internal seams','drawing':'D-001 to D-006','verification':'Connected-envelope line coverage and rendered close-ups'},
 {'comment':'Return branch / its dampers shown without continuous duct walls','correction':'GF-02 return header moved to x=6000; straight room branch to main at y=16400. RG-02-01/02 moved 200 mm to y=17000 for graphic / duct separation. Relocate RCD-R02, FSD-R02 and AD-R02 onto this straight','drawing':'D-003 / D-004; Device_locations / Terminals','verification':'Proposed room geometry; device footprint contained in branch; route / grille coordinates registered'},
 {'comment':'Instrument / component graphics not at the correct duct position','correction':'Check all branch device centres, access sides and rotation against the associated branch profile; connect off-duct temperature / humidity bubbles to their duct probes','drawing':'D-004 to D-007; Device_locations / Instrument_locations','verification':'Geometric attachment checks and visual review'},
]
write('Rev08_corrections.csv',corrections)
print(json.dumps({'revised_sections':list(routes),'supply_and_return_flows':'Retained','new_instrument_IO':'None'}))
