MAIN DUCT AND RETURN — DETAILED REVISION02 — 08 OCTOBER2026

The previous14-sheet issue omitted most detailed plans/registers. This issue
restores the complete engineering content:50 A1 sheets and44 Excel tabs.
Start with Main duct and return - Engineering review.pdf:20 selected sheets
showing actual detailed plans, enlargements, roof/installation/fitting details
and the seven new DX engineering sheets. Full PDF:Main duct and return.pdf.
The three-sheet Method review is now a supporting explanation, not the main
engineering delivery. Editable CAD:Main duct and return.dxf.

DRAWING ORDER
001–032:all32 Rev12 engineering subjects retained and reissued, with the
50-sheet drawing index replacing old D-018. Full plans, room enlargements,
53 terminals, duct/fitting schedules, roof routing,15 drops, crossing/ceiling
sections, fabrication rules,52 path allowance budgets, terminal criteria,
85 instrument mounting specifications, controls/wiring, curbs/supports and
setting-out. Physical route geometry/duties and prior assumptions unchanged.
Original body detail references D-xxx = MDR-xxx on these32 sheets.
033–039:seven NEW DX/header development sheets:dimensioned branch spools,
registered roof split/reducer, drop/curb/firestop, header instruments/drain,
cause-and-effect, wiring/I/O interfaces, equipment duties and commissioning.
040–050:eleven supporting system/method/terminal/instrument diagrams.

REGISTERS
All35 baseline register tabs preserve their cell values and formatting.
Nine additional tabs provide the revised readme,50-sheet drawing index,
85-instrument graphic references, functional header flows,22 DX candidates,
six bank connections, cause/effect, wiring interfaces and equipment schedule.
Original85 instruments,53 terminal tags/neck/face duties and275 I/O unchanged.
The22 DX candidates (7 AI,3 DI,12 OEM-local safeguards) are separate proposals;
factory data or reused fault contacts can change final PLC hardware. No
channels, actual OEM terminals or compressor safety thresholds are assigned.

USER ARCHITECTURE
Common SUPPLY and RETURN mains on the ROOF; nine room supply drops and six
return risers. Three50% DX PAUs connect to the same headers:two duty,one
isolated rotating standby. Prove air paths before start; avoid reverse air
through an idle unit. Refrigeration cools air within the factory DX system;
room ducts carry AIR. Dedicated kitchen/toilet/CAG extracts and basement
ventilation remain separate. Heater/conditional HUM-01 duties are retained
pending final thermal/humidity requirements. Fire stops all fans/heaters,
manual reset; no automatic fire extraction/post-fire purge is added.

HEIGHTS / HOLDS
User slab underside+4.000 m,minimum ceiling+3.300 m. Proposed roof+4.200 m
assumes200 mm slab; roof SA BOD+4.800/RA+5.550 m,75 mm outdoor insulation.
SA main600x1300 / RA700x900 require structure/wind/platform review. Indoor
BOD+3.400 m,max bare depth400,assumed insulation50 and flange25 each face
reserve+3.325..3.875 m:25 mm ceiling gap/125 mm slab allowance. Actual beam,
actuator,heater/plenum/hanger/access envelopes and installed levels pending.
Insulation is an assumption,not a verified UAE specification. RA05 curb is
25 mm outside nominal floor outline:coordinate actual roof/parapet/shaft.
Roof survey,penetrations,weatherproofing,firestop and structure approval open.
New branch700x650 and transition1225/475 mm are dimensioned coordination
proposals; selected PAU ports,flex/damper/tee/offsets and losses remain OEM.

AIR / EQUIPMENT
SA3697.80,assumed RA3006.68 implies minimum makeup691.12 L/s. Earlier
OA420.70 is short270.42; this lower bound is not an approved OA duty.
Known extract212.49,residual478.63 less unresolved CAG extract. Toilet net
-18.69/kitchen0 do not establish+25 Pa. Final leakage/room pressure/comfort/
humidity remain open. DX capacities,refrigerant,nozzles,complete fan ESP and
OEM selections are TBC. The52 retained pressure paths are explicit proposed
route/component allowances,exclude bank/nozzle/OA details and do not select
a fan. No measured leakage or certified diffuser throw/noise is invented.

AUTOCAD
Open Main duct and return.dxf; inspect MDR01_A1..MDR50_A1; Save As DWG.
Keep all mask layers including prefixed copies on; viewport layers do not
plot. Use Arial/Arial Bold and plot lineweights. A1 at100% for stated scales;
NTS diagrams cannot be measured for fabrication. New native dimensions use
scale factors10/20 for dimensioned development. Compare first CAD plot to
PDF. Native AutoCAD plotting/DWG conversion have not run in this cloud.

PORTABLE REBUILD
Python3.12; install source/requirements.txt. From extracted ZIP root:
python source/src/build.py --output-dir generated/main_duct_and_return
python scripts/validate_main_duct_and_return.py
python scripts/package_main_duct_and_return.py
Workbook edits are not imported; edit source/inputs and regenerate.
SHA256.json verifies archive files; external manifest also verifies ZIP.
Original14-sheet delivery is archived under revision-01 in the repository.
Rev08–Rev12 and the original benchmark DWG are preserved.

FOR ENGINEERING COORDINATION — NOT FOR CONSTRUCTION.
Final manufacturer/structural/fire/thermal coordination and approval pending.
