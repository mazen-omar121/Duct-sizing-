# Administration HVAC — Rev08 engineering coordination package

Rev08 corrects the duct connection gaps and component/instrument positions
shown in the three supplied 06 October close-ups. Proposed plan geometry and
register coordinates are synchronized. This remains a coordination issue.

## Deliverables

- **Administration_Detailed_HVAC_Duct_Flow_Diagram.pdf**: 12 vector A1 sheets.
- **Administration_HVAC_Detailed_Layout.dxf**: editable R2013 DXF in millimetres;
  seven plan variants, 22 device blocks and 12 A1 paper-space layouts.
- **Administration_HVAC_Schematic.pdf / .dxf**: four Rev08 schematic sheets;
  supply branch damper order matches the detailed branch station.
- **Administration_HVAC_Drawing_Registers_Rev08.xlsx**: 14-tab drawing-register
  companion with device/probe locations, comment closure and velocity checks.
  It does not replace the earlier HAP/duct calculation workbook.
- **cad-package/**: rebuildable Python source, supplied architecture and design
  inputs, extracted reference vectors, and 11 synchronized CSV registers.
- **drawing_validation.json** and **revision_checks.json**: completed checks.
- **Administration_HVAC_Overview.png** and
  **Administration_HVAC_South_West_Detail.png**: previews.

## Corrections in Rev08

1. Connected duct profiles retain their outside walls. Internal overlap seams
   are opened without erasing coincident exterior lines. Four return-junction
   envelope checks verify continuous walls at the corrected locations.
2. Branch boots attach to the main section whose actual profile contains the
   junction. This corrects return connections adjacent to an enlargement.
3. The GF-02 return collection header moves to **x=6000 mm**. Its room branch
   runs straight from (6000,16400) to (3500,16400). The two upper grilles
   **RG-02-01 and RG-02-02** move 200 mm from y=16800 to **y=17000 mm**.
   Header/runout coordinates and horizontal lengths are updated. These are
   proposed clearance changes, pending ceiling and equipment coordination.
4. Branch dampers and heaters sit on their associated duct straights. Their
   symbol core footprints are checked against the actual branch outline;
   access-door centres are checked on the duct wall. Tags and leaders are
   arranged according to duct orientation. OEM actuator/maintenance envelopes
   and access hatches remain to be coordinated.
5. Common supply/return temperature and return humidity bubbles have leaders
   ending at explicit probes. D-007 shows the common duct walls and common
   heater for context. Five measurement points are checked inside their
   associated main ducts and recorded in **Instrument_locations.csv**.
6. Airflows, selected duct sizes, terminal neck/face sizes and I/O allocations
   are retained. Rev07's tapers, access doors, reference symbols and six
   heater airflow-proof inputs remain in the drawings and registers.

## Sheet index

| Sheet | Drawing | A1 scale |
|---|---|---|
| D-001 | Coordinated duct plan | 1:50 |
| D-002 | Supply air duct plan | 1:50 |
| D-003 | Return air and extract duct plan | 1:50 |
| D-004 | North rooms — enlargement | 1:35 |
| D-005 | South-west rooms — enlargement | 1:25 |
| D-006 | South-east rooms — enlargement | 1:25 |
| D-007 | Room instrumentation locations | 1:50 |
| D-008 | PAU bank and indoor riser section | NTS |
| D-009 | Symbols and installation details | NTS |
| D-010 | Duct and terminal schedules | NTS |
| D-011 | Tapered fittings and maintenance access | NTS |
| D-012 | Plant instrumentation and heater protection | NTS |

Print at **100% / actual size on A1** to preserve the stated scales.

## Symbols and CAD

Supply is green, return blue, dedicated extract brown, outdoor air blue-green,
and instrumentation purple. Red arrows show airflow. Short aliases such as
SD02-1 refer to SD-02-01 in the registers. Main-to-room junction dots identify
connections. Crossings without a junction remain separate duct paths; actual
duct levels and vertical clearance have not been established by this plan.

VCD, MD, MFD, heater and silencer shapes use native vectors extracted from
sheet 2 of the supplied D-113391 reference PDF export. RCD uses the reference
motorized-damper shape with a return-control tag. AD uses a boxed triangle.
Terminal faces retain the Administration schedule dimensions. The original
binary DWG block library was not directly imported or edited. MFD* denotes a
conditional rated-boundary provision; registers retain FSD-prefixed tags.
Approved fire compartmentation governs final device locations and ratings.

Open the detailed DXF and plot layouts **D001_A1 through D012_A1**. Seven
independent `PLAN_...` blocks are placed in model space. Edit their definitions
or explode one selected plan; nested `HVAC_...` device blocks stay reusable.
Keep `M-MASK` enabled for crossings and labels; `VIEWPORT` is non-plotting.
Save a DWG copy in your CAD application if needed. Both DXFs passed ezdxf
audits. Native AutoCAD plotting was not run; compare the first plot with PDF.

## Registers and rebuild

The Excel tabs mirror duct sections, transitions/takeoffs, fittings, terminals,
components, device locations, common probe locations, instruments, I/O,
cause-and-effect and Rev08 corrections. Sizing_check recomputes velocity from
the existing flow and cross-sectional area. Do not sum flows across every duct
section: the same air passes through multiple sections.

With requirements.txt installed, run from this folder:

```bash
python cad-package/src/build_engineering_drawings.py
python cad-package/src/build_schematic.py
python cad-package/src/build_registers.py
```

Update the linked JSON/CSV inputs together before rebuilding. Changes made
only in Excel are not read by the drawing source. Extracted reference vectors
are included; reference extraction is not required for a normal rebuild.
The `update_rev07_registers.py` and `update_rev08_registers.py` scripts record
revision migrations and are not needed to rebuild this completed package.
Running an older migration could restore superseded routes.

## Retained basis and pending engineering inputs

Supply: **3697.80 L/s**. Assumed return: **3006.68 L/s**. Six return rooms retain
the illustrative 0.01 m² equivalent opening area and 59.34 L/s net outward
allowance at the +50 Pa target. These assumed flows do not verify achieved
pressure. Kitchen, toilets and clean-agent target +25 Pa relative to outdoors,
have cooled PAU supply, dedicated extraction and no shared return. GF-07 is a
resting/bed room with return.

Three 50% PAUs use a rotating duty pair and an available alternate. Confirmed
fire stops all HVAC fans and heaters. Automatic fire extraction/purge is not
enabled. Normal ACH references remain 10 for kitchen/toilets and 5 for CAG.

Pending: actual room pressure balance; delivered outdoor air and HAP rerun;
CAG extract duty/quantity and approved post-fire sequence; basement heat duty
and volume; levels, fitting development/K and pressure-loss paths; fan ESP and
curves; terminal throw/noise and catalogue selections; access clearances;
instrument mounting/straight runs; I/O modules, alarm limits and settings.
The retained **420.70 L/s OA** reference is below the **691.12 L/s makeup**
implied by the assumed return balance. This is not a construction issue set.

Taper lengths are proposed plan geometry. They do not establish acceptable
angles, selected pressure losses or fabrication lengths. Equipment/fan
footprints are schematic rather than selected OEM dimensions.
