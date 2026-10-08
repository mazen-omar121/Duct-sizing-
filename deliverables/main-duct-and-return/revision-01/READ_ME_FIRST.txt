MAIN DUCT AND RETURN — METHOD REVISION 01 — 08 OCTOBER 2026

Start with Main duct and return.pdf: 14 A1 sheets. MDR-001 explains the
whole air system; MDR-004 expands the PAU bank; MDR-005 explains DX cooling.
The separate Method review PDF contains those three sheets for quick review.
Editable CAD: Main duct and return.dxf. Registers: Excel, plus three CSVs.

USER SELECTED: common SUPPLY and RETURN mains on the ROOF, with room drops.
Three 50% DX PAUs connect to the same headers: two duty, one rotating standby.
Standby supply/return/outdoor-air paths isolate; duty paths open/prove before
start. DX refrigeration cools air within the selected factory PAU system;
the room mains carry air. Nine supply drops and six return risers are shown.
Kitchen, toilets and clean-agent extracts are separate from recirculated air.

11 new method/instrument/control/section sheets plus 3 clearly labelled
Rev12 physical reference plans. All 53 terminal tags, 85 retained instruments
and 275 original I/O rows remain. Twenty-two new DX candidates are separate
OEM-review proposals; their final channel mapping is not included in that
275-point baseline. Factory safeties may expose contacts/communications rather
than require additional field transmitters. No fixed refrigerant, capacity,
compressor count or safety thresholds are invented. Retained heaters and
conditional HUM-01 serve separate heating/humidity requirements; removal
from cooling-only operation needs a confirmed thermal/humidity design.

MDR-012 is the actual grouped 31-segment Rev12 proposed roof arrangement;
MDR-013 the indoor plan; MDR-014 room instrument locations. Reference pages
retain original Rev12 title blocks and sheet numbering; MDR banners identify
their position in this package. Flow steps SA-M01..09 / RA-M01..06 on the
method diagram are illustrative sequential accounting, not physical segment
tags or a fabrication main schedule. No surveyed roof plan was supplied.
PAU reservations, nozzle interfaces, manifold and common-probe mounting need
OEM development. Use the complete Rev12 package for its remaining details.

USER HEIGHTS: slab/roof underside +4.000 m; minimum ceiling +3.300 m.
PROPOSALS: roof surface +4.200 m assumes a 200 mm slab; roof bare SA BOD
+4.800 m, RA +5.550 m; outdoor insulation 75 mm per face. Roof mains
SA600x1300 and RA700x900 stay outdoors and require structure/wind/platform
review. Indoor room ducts: BOD +3.400 m, bare depth <=400 mm, insulation
50 mm per face assumed. Proposed 25 mm flange allowances reserve +3.325
to +3.875 m: 25 mm ceiling gap, 125 mm slab allowance. Actuators, heaters,
plenums, hangers, beams and access still require actual component checks.
These insulation values are assumptions, not verified UAE requirements.
Installed duct elevations remain unassigned. RA05 curb reservation extends
25 mm outside the nominal floor outline; roof/parapet/shaft setting-out is
an explicit coordination hold. Penetrations/firestops/weather seals need
structural and fire/waterproofing approval.

AIR BALANCE: supply3697.80 minus assumed return3006.68 requires makeup
at least691.12 L/s; earlier OA420.70 is short by270.42 L/s. This is only a
mass-balance lower bound. Known extract212.49, residual478.63 less unknown
CAG extract. Toilet net-18.69 and kitchen0 do not establish +25 Pa. Final
outdoor-air duty, leakage, room pressure and humidity must be resolved.
Fan ESP is not selected from the method diagram. Rev12 provisional path
allowances exclude PAU/nozzle/OA details; OEM coils/filters, discharge,
fitted losses and actual fan curves are pending. No certified terminal
throw/noise or independent room thermal comfort is claimed.

FIRE: confirmed fire stops all fans/heaters, manual reset. No automatic
fire extraction or post-fire purge. Final compressor response, damper
fire positions and safety wiring follow approved OEM/fire requirements.

AUTOCAD: open Main duct and return.dxf, inspect MDR01_A1..MDR14_A1,
Save As DWG. Keep M-MASK on; VIEWPORT/VIEWPORTS nonplotting. Use Arial
and Arial Bold; enable plot lineweights. A1 at 100% for stated section/
plan scales. Most method diagrams are NTS and cannot be measured for
fabrication. Compare your first CAD plot with the PDF. Native AutoCAD
plotting and DWG conversion have not run in this cloud environment.
The reference import preserves all physical-block entities, including masks.
CAD text cap heights and table-header fills are corrected to match the PDF;
duct geometry and preserved source inputs are unchanged. Keep prefixed
M-MASK layers enabled as well as M-MASK; all viewport layers nonplotting.

PORTABLE REBUILD: Python3.12; install source/requirements.txt; run
python source/src/build.py --output-dir generated/main_duct_and_return
from the extracted ZIP root. Then python scripts/validate_main_duct_and_return.py
and python scripts/package_main_duct_and_return.py. The source is preserved;
generated workbook edits are not imported. SHA256.json verifies package
files; the external manifest additionally verifies the ZIP itself.

FOR ENGINEERING COORDINATION — NOT FOR CONSTRUCTION.
Actual roof survey, OEM selections, structure and final engineering approval
remain pending. Rev08–Rev12 source/deliveries and the user's reference DWG
are preserved in the repository.
