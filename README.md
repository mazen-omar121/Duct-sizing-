# HVAC duct drawing and sizing project

The current delivery is **Rev12: 32 detailed A1 sheets, four functional schematic sheets, editable DXF and 35-tab Excel registers**. It adds roof routing and drop sections, fitting development, 52 pressure-path estimates, fan budgets, air balance, terminal selection criteria, all 85 instrument installation specifications, wiring interfaces, curbs/supports and ceiling component envelopes.

Download the [complete Rev12 ZIP](deliverables/rev12/Administration_HVAC_Rev12.zip?raw=true) or review the [ten new engineering sheets](deliverables/rev12/Administration_HVAC_Junction_Review_Rev12.pdf). [Full color PDF](deliverables/rev12/Administration_HVAC_Detailed_Drawings_Rev12.pdf), [monochrome PDF](deliverables/rev12/Administration_HVAC_Detailed_Drawings_Rev12_Monochrome.pdf) and [Excel registers](deliverables/rev12/Administration_HVAC_Drawing_Registers_Rev12.xlsx?raw=true) are available individually. GitHub: select **Download raw file** if needed.

The 31 proposed roof segments connect 15 room drops, with 11 registered supply/return plan overlaps at separate levels and no return riser through the lower supply routes. The retained 116 indoor paths have no bare/insulated independent-service crossings. Room duties, terminal necks/faces, 85 instruments and I/O remain unchanged. See [exact scope and assumptions](projects/administration_rev12/REVISION_12.md).

User confirmed +4.000 m slab underside, +3.300 m minimum ceiling and roof distribution. Roof levels, 200 mm slab thickness, 75 mm outdoor insulation, PAU reservation footprints and all fitting/component loss allowances are provisional. Rooftop nozzle/manifold/OA and exhaust discharge losses, wind/load/structure, actual equipment envelopes, catalogue throw/noise and final electrical interfaces remain open. No fan is selected. The mass-balance makeup 691.12 L/s exceeds OA reference 420.70 L/s; toilet/kitchen pressure targets are not established. **For engineering coordination, not for construction.** Rev08–Rev11 sources and deliveries are preserved.

Open `Administration_HVAC_Detailed_Layout_Rev12.dxf` in AutoCAD, review **D001_A1 through D032_A1**, then **Save As → DWG**. Keep `M-MASK` enabled, `VIEWPORT` nonplotting and use Arial. Print A1 at actual size for stated scales. NTS details must not be scaled. Native AutoCAD plotting has not run here; compare the first plot to the PDF.

Rebuild in the cloud:

```bash
python3 -m venv /workspace/.venvs/administration-cad
/workspace/.venvs/administration-cad/bin/python -m pip install -r projects/administration_rev12/requirements.lock.txt
/workspace/.venvs/administration-cad/bin/python scripts/build_administration.py
/workspace/.venvs/administration-cad/bin/python scripts/validate_administration.py
/workspace/.venvs/administration-cad/bin/python scripts/package_administration.py
/workspace/.venvs/duct-cad/bin/python -m unittest discover -s tests
/workspace/.venvs/duct-cad/bin/python app.py
```

App dependencies: `requirements.txt`; CAD dependencies: locked project file above. Use `app.py --port 5005` (or another available port). An optional licensed ODA File Converter configured via `DUCT_ODA_CONVERTER` enables server DWG export; AutoCAD users can save the DXF directly as DWG without that converter.

The build wrapper stages source inputs, preserving edited files and the last successful build if generation fails. Outputs are in ignored `generated/administration/`; packaging writes `generated/delivery/`. Validated delivery copies go in `deliverables/rev12/`. Run one build at a time. Historical migration scripts are not normal build steps and must not be rerun over edited source.

Validation checks both CAD audits, 32 color/monochrome A1 sheets, four schematic sheets, 24 native dimensions, instrument tag references, indoor geometry/flow/headroom, roof graph conservation, independent roof insulation/shaft checks, delivered roof exteriors, all 52 pressure arithmetic paths, 53 terminal screens, 85 installation rows, support spacing and workbook consistency. No native AutoCAD plot or structural/OEM certification is claimed.
