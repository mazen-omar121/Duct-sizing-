# Main duct and return — detailed revision 02

The previous issue explained the system but omitted most detailed plans and engineering registers. Revision02 restores that content: **50 A1 sheets and 44 Excel tabs**, with the detailed drawings first. Roof common supply/return mains and room drops remain the user's selected arrangement; the air is cooled by the DX PAU bank.

[View the full drawings](../../deliverables/main-duct-and-return/Main%20duct%20and%20return.pdf), [review 20 detailed engineering sheets](../../deliverables/main-duct-and-return/Main%20duct%20and%20return%20-%20Engineering%20review.pdf) or [download the complete ZIP](../../deliverables/main-duct-and-return/Main%20duct%20and%20return.zip?raw=true). [Editable DXF](../../deliverables/main-duct-and-return/Main%20duct%20and%20return.dxf?raw=true) and [Excel registers](../../deliverables/main-duct-and-return/Main%20duct%20and%20return%20-%20Registers.xlsx?raw=true) are available separately. The three-sheet method review remains a supporting explanation.

| Sheets | Restored or added content |
| --- | --- |
| MDR-001–006 | Full coordinated, supply, return/extract plans and three room enlargements |
| MDR-007–017 | Room/plant/fan instruments, PAU distribution, installation symbols, duct/terminal schedules, tapered fittings, heater protection, controls and setting-out |
| MDR-018 | Complete 50-sheet index replacing the earlier drawing index |
| MDR-019–025 | Actual junction enlargements, ceiling envelopes, recorded changes, all15 drops, detailed roof routing, crossing/drop sections and fitting development |
| MDR-026–032 | Pressure/fan allowance budgets, air balance, terminal selection, instrument mounting/wiring, roof curbs/supports, component access and roof dimensions |
| MDR-033 | New DX unit branch/header transition plans/elevations, native dimensions and six connection records |
| MDR-034 | Registered roof split and reducer development, open throats and construction/access requirements |
| MDR-035 | Dimensioned telecom supply/return drop, roof curb, weather/firestop and ceiling coordination |
| MDR-036 | Common-header measurement stations, sensor/tap access and DX condensate/drain requirements |
| MDR-037 | DX/fan/damper/fire cause-and-effect matrix covering all22 DX candidate tags |
| MDR-038 | OEM/HPCP wiring interfaces and all22 candidate channels, explicitly unassigned |
| MDR-039 | DX equipment duties, nine-room airflow/TAB records and procurement/commissioning holds |
| MDR-040–050 | Eleven supporting whole-system, room terminal, extract, PAU, DX, safety and instrument diagrams |

The original32 engineering subjects are retained, with the drawing index replaced and the title blocks reissued as **Main duct and return / revision02**. The physical routes, wall geometry, terminal duties and original design assumptions are unchanged. Retained body references `D-xxx` correspond to the same `MDR-xxx` number on sheets001–032. New details develop the DX/common-header method; nozzle/manifold geometry and installed equipment dimensions still require the selected OEM. NTS diagrams and proposed spool development are not fabrication release drawings.

**44 register tabs:** all35 baseline tabs retain their cell values and formatting, plus nine new tabs for the revised readme, drawing/instrument index, functional flow accounting, DX candidates, six bank connections, cause/effect, wiring interfaces and equipment selection. All53 terminals,85 retained instruments and275 original I/O rows remain. The22 separate DX candidates comprise7 AI,3 DI and12 OEM-local protections; factory data/reused fault contacts may change the actual additional panel count.

The three PAUs connect to the same headers: two50% duty units and one isolated rotating standby. Cooling refrigerant stays within the factory DX system; air ducts serve the rooms. Nine supply drops and six return risers are retained. Toilet/kitchen/clean-agent extracts and basement ventilation remain separate. Heating and conditional HUM-01 requirements are retained pending thermal/humidity design.

Open `Main duct and return.dxf` in AutoCAD, inspect **MDR01_A1 through MDR50_A1**, then **Save As → DWG**. All mask layers, including `$0$`-prefixed imports, must be on; viewport layers are nonplotting. Arial/Arial Bold, plot lineweights and A1 at100% for stated scales. Model blocks retain original building millimetres; supporting diagrams use drawn paper millimetres. Compare the first CAD plot with the PDF. Native AutoCAD plotting/conversion has not run here.

**Engineering coordination issue.** User slab underside+4.000 m and minimum ceiling+3.300 m remain. Roof surface+4.200 m, outdoor75/indoor50 mm insulation, flange/support/curb and equipment reservations are proposals. RA05 curb extends25 mm beyond the nominal floor outline; roof/parapet/shaft coordination is open. Installed duct elevations, selected OEM dimensions, DX capacity/refrigerant, complete fan ESP, structure/fire approval and final engineering review remain pending. Minimum makeup691.12 L/s exceeds OA reference420.70 by270.42; CAG extract, toilet/kitchen pressure and independent room comfort/humidity remain unresolved. No selected fan, measured leakage, thermal compliance or certified terminal throw/noise is claimed.

Rebuild with Python3.12:

```bash
/workspace/.venvs/administration-cad/bin/python -m pip install -r projects/main_duct_and_return/requirements.txt
/workspace/.venvs/administration-cad/bin/python projects/main_duct_and_return/src/build.py
/workspace/.venvs/administration-cad/bin/python scripts/validate_main_duct_and_return.py
/workspace/.venvs/administration-cad/bin/python scripts/package_main_duct_and_return.py
/workspace/.venvs/duct-cad/bin/python -m unittest discover -s tests
```

Generated outputs are in `generated/main_duct_and_return/`; packaging validates before copying to `deliverables/main-duct-and-return/`, which the app serves. In the extracted ZIP, install `source/requirements.txt`, then run `python source/src/build.py --output-dir generated/main_duct_and_return`, `python scripts/validate_main_duct_and_return.py` and `python scripts/package_main_duct_and_return.py` from the extracted root. Workbook edits are not imported. Run one build at a time. Input SHA256 provenance and archive/delivery manifests are included. The original14-sheet issue is preserved in `deliverables/main-duct-and-return/revision-01/`; Rev08–Rev12 and the user's benchmark DWG remain unchanged.
