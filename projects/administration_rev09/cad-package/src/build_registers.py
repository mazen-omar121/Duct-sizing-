"""Create the Rev08 drawing-register Excel companion from the authoritative CSVs."""
from pathlib import Path
import csv,json
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Font,PatternFill,Alignment,Border,Side
from openpyxl.worksheet.table import Table,TableStyleInfo
from openpyxl.utils import get_column_letter
BASE=Path(__file__).resolve().parents[1];OUT=BASE.parent
wb=Workbook();intro=wb.active;intro.title='Read_me'
readme=[
 ('ADMINISTRATION HVAC - REV09 DRAWING REGISTERS','07 October 2026 | engineering coordination issue'),
 ('Purpose','Excel companion to the revised drawings. This is a drawing register and sizing cross-check; it does not replace the earlier HAP/duct calculation workbook.'),
 ('Supply basis','3697.80 L/s total; room airflows and selected section sizes retained from Rev05.'),
 ('Return basis','3006.68 L/s assumed total; achieved pressure remains unverified.'),
 ('Pressure targets','+50 Pa normal / return rooms; +25 Pa kitchen, toilets and clean-agent, relative to outdoors.'),
 ('Room connections','Clean-agent, kitchen and toilets have cooled PAU supply, dedicated extract and no shared return. GF-07 is a resting/bed room with return.'),
 ('Plant / fire','PAUs: 3 x 50%, rotating pair of two duty units. Confirmed fire stops all HVAC fans and heaters.'),
 ('Drawing comments','See Comment_closure for the visible screenshot corrections and their drawing references.'),
 ('Duct sections','One row per main, branch, header or terminal runout. Do not sum all section flows: the same air passes through several sections.'),
 ('Lengths','Horizontal lengths are proposed centreline allowances. Rev08 route changes are recorded. Vertical lengths, developed fittings and elevations remain TBC.'),
 ('Sizing_check','Recomputed cross-sectional area and velocity using the existing flow and section sizes. The tab does not select new sizes.'),
 ('Transitions','13 main tapers, 15 room branch boots and 49 external terminal adaptors have explicit proposed plan geometry. SD-07-01 and RG-05-05 use short direct / integral plenum conversions; see D-009 / D-011.'),
 ('Access / instruments','21 duct access doors; 85 instruments including six explicit heater airflow-proof DI inputs. OEM safety remains hardwired independently of PLC demand.'),
 ('Rev08 locations','Branch device bodies checked within their ducts; AD centres checked on the duct wall. Probe_locations records five common duct instrument attachments. All positions are proposed pending levels and OEM clearances.'),
 ('GF-02 route change','Return collection header moved to x=6000 mm; branch is straight at y=16400 mm. RG-02-01 and RG-02-02 move 200 mm to y=17000 mm. Runout/header lengths are synchronized; flows and neck/face sizes are retained.'),
 ('I/O','65 AI, 22 AO, 141 DI, 44 DO; three COMM interfaces. 20% spare is rounded up by signal class; module allocation remains pending.'),
 ('Holds','Actual room pressure balance, outdoor-air compliance / HAP rerun, CAG and basement duties, catalogue selections, fitting K, fan ESP, levels and final control settings remain open.'),
 ('Rev09 drawing detail','18 detailed A1 sheets; 85 tagged instruments; native plan dimensions; complete instrument drawing index. Rev08 duties and section sizes retained.'),
 ('How to edit','Revise the linked JSON / CSV inputs together and regenerate PDF, DXF and this workbook. The drawing source does not read edits made only in this Excel companion.'),
]
for row in readme:intro.append(row)
intro.column_dimensions['A'].width=28;intro.column_dimensions['B'].width=115
for row in intro:
 for c in row:c.alignment=Alignment(vertical='top',wrap_text=True);c.font=Font(name='Calibri',size=11,color='192633')
 intro.row_dimensions[row[0].row].height=45 if row[0].row>1 else 30
for c in intro[1]:c.fill=PatternFill('solid',fgColor='123B52');c.font=Font(name='Calibri',size=14,bold=True,color='FFFFFF')
intro.freeze_panes='B2'

maps=[('Duct_sections.csv','Duct_sections'),('Transitions_and_takeoffs.csv','Transitions'),('Fittings.csv','Fittings'),('Terminals.csv','Terminals'),('Components.csv','Components'),('Device_locations.csv','Device_locations'),('Instrument_locations.csv','Probe_locations'),('Instruments.csv','Instruments'),('IO_points.csv','IO_points'),('Cause_and_effect.csv','Cause_effect'),('Rev08_corrections.csv','Rev08_corrections'),('Instrument_drawing_index.csv','Instrument_drawing_index')]
for filename,title in maps:
 ws=wb.create_sheet(title)
 with (BASE/'schedules'/filename).open() as f:
  reader=csv.reader(f)
  for row in reader:
   vals=[]
   for val in row:
    # Preserve identifiers, room numbers and unresolved entries as text.
    vals.append(val)
   ws.append(vals)

ws=wb.create_sheet('Sizing_check')
ws.append(['Section','Air','Room','Flow L/s','Width mm','Height mm','Diameter mm','Area m2','Velocity m/s','Scheduled m/s','Difference m/s','Length m','Basis'])
from math import pi,ceil
rows=list(csv.DictReader((BASE/'schedules/Duct_sections.csv').open()))
for r in rows:
 q=float(r['flow_l_s']);w=float(r['width_mm']);d=float(r['diameter_mm']) if r['diameter_mm'] else None;h=float(r['height_mm']) if r['height_mm'] else None
 area=pi*(d/1000)**2/4 if d else w*h/1e6;v=q/1000/area;old=float(r['velocity_m_s'])
 ws.append([r['tag'],r['air_type'],r['room'],q,w,h,d,area,v,old,v-old,float(r['horizontal_length_m']),'Retained size / airflow; recalculated velocity only'])
 assert abs(v-old)<.00002,(r['tag'],v,old)
 for c in ws[ws.max_row][3:12]:c.number_format='0.000'

ws=wb.create_sheet('Comment_closure')
ws.append(['Comment','Rev08 action','Drawing / register','Status'])
for row in [
 ('Outside walls missing at connected joints','Preserved the outside envelope of the connected duct profiles; removed internal seams only','D-001 to D-006; geometry validation','Corrected; four marked-junction checks passed'),
 ('GF-02 return branch crossed its own header','Moved header to x=6000 mm and made branch straight at y=16400 mm; two upper grilles moved +200 mm','D-003 / D-004; Duct_sections / Terminals','Proposed positions registered; levels and ceiling coordination pending'),
 ('Branch dampers / heaters outside duct straight','Repositioned branch devices and verified each core footprint within its associated duct; AD centres on duct wall','D-004 to D-006; Device_locations','Drawing geometry checked; OEM access envelopes pending'),
 ('Duct sensor tags lacked measurement connections','Added probe leaders and common-duct context; verified five measurement points inside their assigned main ducts','D-007; Probe_locations','Proposed probe attachment checked; OEM mounting pending'),
 ('Device tags overlapped duct symbols','Placed tags according to duct orientation and separated access-door leaders','D-004 to D-006','Revised enlarged views visually checked'),
 ('Earlier transition / access / heater proof provisions','Retained 13 main tapers, 15 room boots, 49 external adaptors, 21 AD tags and six AFS-EH inputs from Rev07','D-008 / D-009 / D-011 / D-012; Transitions / IO_points','Retained; no new airflow or I/O allocation in Rev08'),
]:ws.append(row)

for index,ws in enumerate(wb.worksheets[1:],1):
 ws.freeze_panes='A2';ws.sheet_view.showGridLines=False
 ws.print_title_rows='1:1';ws.sheet_properties.pageSetUpPr.fitToPage=True
 ws.page_setup.orientation='landscape';ws.page_setup.paperSize=ws.PAPERSIZE_A3;ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=0
 ws.auto_filter.ref=ws.dimensions
 for c in ws[1]:c.fill=PatternFill('solid',fgColor='123B52');c.font=Font(name='Calibri',size=10,bold=True,color='FFFFFF');c.alignment=Alignment(wrap_text=True,vertical='center')
 ws.row_dimensions[1].height=34
 for row in ws.iter_rows(min_row=2):
  for c in row:c.alignment=Alignment(vertical='top',wrap_text=True);c.font=Font(name='Calibri',size=10,color='192633')
  ws.row_dimensions[row[0].row].height=46 if ws.title in ['Instruments','IO_points','Cause_effect','Comment_closure','Rev08_corrections','Probe_locations'] else 32
 for j,col in enumerate(ws.iter_cols(),1):
  maximum=max(len(str(c.value or '')) for c in col);width=min(65,max(14,maximum*.8))
  ws.column_dimensions[get_column_letter(j)].width=width
 for row in ws.iter_rows(min_row=2):
  lines=max(sum(max(1,ceil(len(line)/(ws.column_dimensions[c.column_letter].width*.85))) for line in str(c.value or '').split('\n')) for c in row)
  ws.row_dimensions[row[0].row].height=max(30,lines*14+8)
 tab=Table(displayName='HVAC_'+str(index),ref=ws.dimensions);tab.tableStyleInfo=TableStyleInfo(name='TableStyleMedium2',showRowStripes=True)
 ws.add_table(tab)
 ws.sheet_properties.tabColor='228B22' if ws.title in ['Duct_sections','Transitions','Sizing_check'] else '703779' if ws.title in ['Instruments','IO_points','Cause_effect'] else '123B52'
wb.save(OUT/'Administration_HVAC_Drawing_Registers_Rev09.xlsx')
check=load_workbook(OUT/'Administration_HVAC_Drawing_Registers_Rev09.xlsx')
assert check['Duct_sections'].max_row==len(rows)+1
assert check['Instruments'].max_row==86
print(json.dumps({'Excel_sheets':len(wb.worksheets),'velocity_checks':len(rows),'registers':'Matched drawing CSVs'}))
