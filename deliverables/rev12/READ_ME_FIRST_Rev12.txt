ADMINISTRATION HVAC — REV12 ENGINEERING DEVELOPMENT

Start with Administration_HVAC_Junction_Review_Rev12.pdf: ten new sheets,
D-023 through D-032 covering roof plan, sections, fitting rules, pressure
budgets, air balance, terminal selection, instrumentation/wiring, curbs,
supports, component envelopes and setting-out. Full PDF: 32 A1 sheets;
functional schematic: four sheets; workbook: 35 tabs.

31 proposed roof route segments connect 15 room drops. Eleven supply/return
plan overlaps have separate levels, minimum 150 mm insulation gap; no return
riser intersects the lower supply routes in this proposal. Roof geometry is
based on the supplied floor footprint, not a roof/structural survey.
RA05 curb reservation extends 25 mm beyond the nominal floor-plan outline:
roof/parapet and shaft/opening setting-out must be revised or confirmed.
PAU reservation footprints and dashed nozzle/manifold interfaces need OEM
confirmation; their detailed connection losses are not included.

USER BASIS: slab/roof underside +4.000 m; minimum ceiling +3.300 m.
PROPOSALS: roof surface +4.200 m assumes 200 mm slab; bare roof supply BOD
+4.800 m, return +5.550 m; outdoor insulation 75 mm each face. Tall roof mains
and supports need wind/load/maintenance-platform design. Indoor BOD +3.400 m,
50 mm insulation assumed; adding 25 mm flange allowance leaves the deepest
duct at +3.325 to +3.875 m: 25 mm ceiling gap, 125 mm slab allowance.
OEM casing, actuator, hanger, beam and access checks remain pending.

52 terminal pressure paths and fan budgets use measured proposed lengths,
provisional rises and explicitly assumed K/component losses, with sensitivity.
No OEM fan or certified diffuser throw/noise is selected. All 53 terminals
have selection criteria; all 85 instruments have installation specifications.
The original terminal duties, instrument requirements and I/O are retained.

Minimum mass-balance makeup: 691.12 L/s, versus OA reference 420.70 L/s.
Resolve this 270.42 L/s shortfall and room-pressure/extract conflicts.
CAG extract duty is unresolved; toilet net -18.69 L/s and kitchen zero do not
establish +25 Pa. See the registers and REVISION_12.md for exact assumptions.

Open Administration_HVAC_Detailed_Layout_Rev12.dxf in AutoCAD; review
D001_A1 through D032_A1, then Save As DWG. Keep M-MASK enabled; VIEWPORT
is nonplotting; text uses Arial. Print A1 at actual size for stated scales;
do not scale NTS details. Native AutoCAD plotting has not run in this cloud.

Portable rebuild: Python 3.12, install source/requirements.txt; run
source/cad-package/src/design_rev12.py, build_engineering_drawings.py,
build_schematic.py and build_registers.py in that order. Generators rewrite
derived schedules; preserve edited inputs. The root project wrapper stages
an isolated copy and validates before replacing the previous outputs.

FOR ENGINEERING COORDINATION — NOT FOR CONSTRUCTION.
Roof survey, structural/fire/waterproofing approval, OEM selection and final
engineering review remain open. Prior revisions and reference DWG retained.
