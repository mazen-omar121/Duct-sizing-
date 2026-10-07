"""Idempotent Rev07 coordination changes: routes, access and heater proof."""
from pathlib import Path
from math import hypot
import csv,json
BASE=Path(__file__).resolve().parents[1]
def read(name):return list(csv.DictReader((BASE/'schedules'/name).open()))
def write(name,rows):
 with (BASE/'schedules'/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

sections=read('Duct_sections.csv')
routes={
 'SA-B01':[(18500,9300),(18500,8800),(16800,8800),(16800,3500)],
 'SA-B06':[(11000,9300),(11000,10600),(11800,10600)],
 'SA-H06-D01':[(11800,10600),(11800,6000)],
 'SA-R06-01':[(11800,10600),(5400,10600),(5400,9800)],
 'SA-R06-02':[(11800,10600),(14700,10600),(14700,9800)],
 'RA-B06':[(13000,10200),(13600,10200),(13600,7700),(11300,7700),(11300,8350)],
 'RA-H06-D01':[(13000,5600),(13000,10200)],
 'RA-R06-01':[(3100,8550),(3100,10200),(13000,10200)],
 'RA-R06-02':[(9700,8550),(9700,10200),(13000,10200)],
 'RA-R06-03':[(17200,8550),(17200,10200),(13000,10200)],
}
for r in sections:
 if r['tag'] in routes:
  p=routes[r['tag']];r['points_mm']=json.dumps(p)
  r['horizontal_length_m']=str(round(sum(hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(p,p[1:]))/1000,3))
  r['route_basis']='Rev07 proposed clearance route; avoids coincident mains / allows branch-device station. Levels and developed fitting length TBC'
write('Duct_sections.csv',sections)

components=read('Components.csv');known={r['tag'] for r in components}
for prefix,ids in [('AD-S',['02','05','04','08','06','07','09','03','01']),('AD-R',['02','05','04','08','06','07']),('AD-H',['04','05','06','07','03','COM-01'])]:
 for rid in ids:
  tag=prefix+rid
  if tag not in known:components.append({'tag':tag,'service':'Duct access door for inspection / maintenance','basis':f'Rev07 reference drafting convention; adjacent branch damper / heater {rid}','selection_status':'Proposed location; access side / clear opening / ceiling hatch / OEM clearance TBC'})
write('Components.csv',components)

instruments=read('Instruments.csv');io=read('IO_points.csv');known={r['tag'] for r in instruments}
for rid in ['04','05','06','07','03','COM-01']:
 tag='AFS-EH-'+rid
 if tag not in known:
  instruments.append({'tag':tag,'parameter':'Airflow proving switch for heater safety permissive','location':'Electric heater EH-'+rid,'io':'DI','basis':'Explicit Rev07 OEM safety / monitoring provision; not a quoted additional TAQA minimum','provision':'Proposed; OEM proof technology / setpoint TBC','action':'Hardwired heater inhibit on loss of airflow; status / alarm to HPCP. Independent TSHH high limit remains active'})
  io.append({'tag':tag,'type':'DI','signal':'Heater airflow proof healthy / failed','action':'Heater enable inhibited unless airflow is proved; hardwired OEM safety circuit and PLC status','basis':'Rev07 explicit heater airflow-proof provision; confirm OEM interface','status':'Draft allocation; OEM / I&C confirmation pending'})
write('Instruments.csv',instruments);write('IO_points.csv',io)
cause=read('Cause_and_effect.csv')
for r in cause:
 if r['trigger']=='Heater high limit / no flow':r['input']='TSHH / AFS';r['equipment_action']='Heater OFF by OEM hardwired safety; alarm / proof status to PLC'
write('Cause_and_effect.csv',cause)
print(json.dumps({'components':len(components),'instruments':len(instruments),'new_access_doors':21,'heater_proof_DI':6,'io_counts':{t:sum(r['type']==t for r in io) for t in ['AI','AO','DI','DO','COMM']},'revised_branch_routes':routes}))
