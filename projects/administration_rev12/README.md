# Administration HVAC Rev12

See [REVISION_12.md](REVISION_12.md) for the exact engineering scope and assumptions and [READ_ME_FIRST.txt](READ_ME_FIRST.txt) for AutoCAD and rebuild instructions.

Authoritative editable inputs are in `cad-package/inputs/` and `cad-package/schedules/`. The root build wrapper copies them to staging and runs the generators. Rev12 roof / loss / installation assumptions are defined in `cad-package/src/design_rev12.py`; its Engineering_basis_Rev12 JSON and Rev12 CSVs are generated outputs. Edit the source assumptions to revise them, then rebuild and re-coordinate the sheet details. Derived Rev12 CSVs are reproducible; do not treat a workbook-only edit as an input update.

No OEM equipment model or structural roof survey is available. Keep provisional values explicit until manufacturer/site data replace them; do not turn an assumed calculation into an approval claim.
