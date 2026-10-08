# Main duct and return

Method revision 01, 8 October 2026. This separate option explains **a DX PAU bank feeding common roof supply and return mains, with room drops**. The user's selected roof arrangement, +4.000 m structural underside and +3.300 m minimum ceiling are retained. Rev08–Rev12 remain available.

Download the [complete package](../../deliverables/main-duct-and-return/Main%20duct%20and%20return.zip?raw=true), [14-sheet PDF](../../deliverables/main-duct-and-return/Main%20duct%20and%20return.pdf), [editable DXF](../../deliverables/main-duct-and-return/Main%20duct%20and%20return.dxf?raw=true) or [registers](../../deliverables/main-duct-and-return/Main%20duct%20and%20return%20-%20Registers.xlsx?raw=true).

All three PAUs connect to the same headers; two 50% units operate while one is isolated on rotating standby. DX refrigeration cools the air inside the PAUs. Air ducts deliver that air to nine rooms; six return branches collect it. Kitchen, toilet and clean-agent extracts remain separate. The original 53 terminals, 85 instruments and 275 I/O rows are retained. The 22 additional DX protection/monitoring candidates are explicitly separate proposals for OEM review.

| Sheet | Content |
| --- | --- |
| MDR-001 | Whole system: PAU bank, common headers, every room drop, dampers and flows |
| MDR-002 | All 53 terminal tags and connected room supply/return/extract headers |
| MDR-003 | Separate extracts with connected inlet/outlet headers and duty/standby fans |
| MDR-004 | Three PAU air paths, mixed outdoor/return air, filters, DX coils, fans and air-side instruments |
| MDR-005 | DX refrigerant cycles, 21 unit protection/monitoring candidates and optional common static control |
| MDR-006 | All 27 room temperature, humidity and pressure instruments |
| MDR-007 | Six retained heater airflow/high-limit protections and hardwired safety chain |
| MDR-008 | Roof crossing section, indoor ceiling envelope and all 15 riser levels/sizes |
| MDR-009 | Basement instruments, energy meter, HPCP and operating/fire sequence |
| MDR-010 | All 85 retained instruments indexed to their graphical sheets |
| MDR-011 | Transparent functional header flow accounting, velocity/friction and selection holds |
| MDR-012 | Retained Rev12 scaled roof routing proposal, D-023 |
| MDR-013 | Retained Rev12 scaled indoor coordination plan, D-001 |
| MDR-014 | Retained Rev12 room instrument locations, D-007 |

The first 11 sheets explain the method. Distribution diagrams are NTS; the sections on MDR-008 carry their own vertical scales. The last three sheets are clearly labelled references retaining their original Rev12 title blocks. Their actual grouped roof takeoffs and 31 registered segments govern the physical proposal. The 15 sequential accounting steps on MDR-001/MDR-011 explain flow conservation and are **not a fabrication main schedule**. The roof bank/nozzle connections remain functional interfaces pending actual OEM dimensions.

The CAD reference import preserves every entity in the physical model blocks, including masks. Presentation corrections convert PDF font sizes to CAD cap heights and restore pale table-header fills; source inputs and duct coordinates are unchanged. Source mask/dash resources may have a `$0$` prefix to keep their original settings.

Open `Main duct and return.dxf` in AutoCAD, inspect **MDR01_A1 through MDR14_A1**, then **Save As → DWG**. Keep all `M-MASK` layers, including prefixed copies, on and all viewport layers nonplotting. Text uses Arial/Arial Bold; install those fonts or select metrically compatible substitutes. Plot A1 at 100%, enable plot lineweights, and compare the first plot to the PDF. DXF coordinates are millimetres; NTS diagrams use drawn paper millimetres, while retained plan blocks use original building millimetres. Do not measure fabrication dimensions from the functional diagrams. Native AutoCAD plotting/conversion has not run here.

**Engineering coordination issue.** DX capacity/refrigerant/OEM equipment, complete fan ESP, actual roof/structural survey, penetrations, final duct elevations, insulation specification and fire/wiring approval remain pending. The retained supply 3697.80 L/s and assumed return 3006.68 L/s imply a minimum makeup 691.12 L/s; the earlier OA reference 420.70 L/s is short by 270.42 L/s. This lower bound is not an approved ventilation selection. Toilet/kitchen pressure targets and CAG extract remain unresolved. See `READ_ME_FIRST.txt` for the known RA05 curb/roof-edge hold and ceiling allowances. No fan, refrigeration circuit safety setting or pressure compliance is certified.

Rebuild from the repository using Python 3.12:

```bash
python3 -m venv /workspace/.venvs/administration-cad
/workspace/.venvs/administration-cad/bin/python -m pip install -r projects/main_duct_and_return/requirements.txt
/workspace/.venvs/administration-cad/bin/python projects/main_duct_and_return/src/build.py
/workspace/.venvs/administration-cad/bin/python scripts/validate_main_duct_and_return.py
/workspace/.venvs/administration-cad/bin/python scripts/package_main_duct_and_return.py
```

The builder uses only this project's preserved inputs. Generated files go to `generated/main_duct_and_return/`; packaging independently validates them and copies the reviewed files to `deliverables/main-duct-and-return/`. The app serves those published copies. Edit source/inputs, then regenerate; workbook edits are not imported. Run one build at a time. `PROVENANCE.json` identifies the baseline and source hashes. The ZIP includes the source, reference inputs, validation/package scripts and checksum manifest for a portable rebuild.
