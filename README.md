# Administration HVAC drawing app

The current delivery is **Rev11, a roof-distribution design option for 3.30 m clear height below a 4.00 m slab**. It contains 22 detailed A1 sheets, four functional schematic sheets, editable DXF, Excel registers and reproducible source. Roof option selection and actual roof routing / structural penetrations remain pending.

Download the [complete Rev11 ZIP](deliverables/rev11/Administration_HVAC_Rev11.zip?raw=true). Start with the [four-page engineering review](deliverables/rev11/Administration_HVAC_Junction_Review_Rev11.pdf): D-019 actual junction enlargements, D-020 ceiling envelope, D-021 changes and D-022 proposed roof drops. The [full color drawings](deliverables/rev11/Administration_HVAC_Detailed_Drawings_Rev11.pdf), [monochrome edition](deliverables/rev11/Administration_HVAC_Detailed_Drawings_Rev11_Monochrome.pdf) and [Excel registers](deliverables/rev11/Administration_HVAC_Drawing_Registers_Rev11.xlsx?raw=true) are also available individually. On GitHub select **Download raw file** if needed.

Rev11 replaces the deep indoor common mains with a proposed roof distribution system and 15 independent room drops. Electrical and telecom returns use perimeter trees. The 116 indoor paths form nine supply, six return and two extract room networks, with no bare indoor crossings, insulated separate-service overlaps, unintended same-service intersections or retraced centerlines. All scheduled terminal duties, neck/face sizes, 85 instrument requirements and I/O duties are retained. Thirteen additional terminal position proposals and twenty existing section size changes are documented against Rev10.

The proposed indoor bare BOD is **+3.400 m**, with a maximum bare depth of **400 mm** and assumed **50 mm insulation each face**. The deepest insulated envelope is +3.350 to +3.850 m, giving 50 mm above the required ceiling and 150 mm below the slab. This is a **duct envelope check**; selected flanges, supports, actuators, heater casings, terminal plenums and access may require local redesign. The 50 mm ceiling gap is not a general plenum or working clearance. Insulation is an assumption, not a verified UAE standard, and installed BOD remains unassigned.

Roof common-main sizes/flows are functional only. Actual roof routes, levels, lengths, outdoor insulation, structural openings, curbs, weatherproofing and loads remain to be designed from site information. Common heater / conditional humidifier / five probes are proposed in weather-protected roof plant; OEM suitability and physical mounting are pending. No roof clash clearance or slab penetration approval is claimed.

Pressure / outdoor-air balance, revised fitting losses / fan ESP / curves, OEM terminal performance, fire boundaries and I&C settings / wiring remain open. Toilet net flow -18.69 L/s and kitchen zero do not establish +25 Pa. **For engineering coordination, not for construction.** See [REVISION_11.md](projects/administration_rev11/REVISION_11.md). Rev08 / Rev09 / Rev10 source and deliveries remain intact; Rev10 CX-08 at +2.050 m does not meet the new ceiling requirement.

## AutoCAD workflow

Extract the ZIP and open `Administration_HVAC_Detailed_Layout_Rev11.dxf` in AutoCAD. Review **D001_A1 through D022_A1**, then **Save As → DWG**. Keep `M-MASK` enabled; `VIEWPORT` is non-plotting. Text uses Arial. Print A1 PDFs at 100% / actual size for stated scales; D-019 shows each detail's 1:20 or 1:25 scale. NTS details must not be scaled. Native AutoCAD plotting has not been run here; compare the first plot against the supplied PDF.

A server converter is optional for server-side DWG downloads; it is not needed when you use AutoCAD. No converter is installed and direct server DWG generation remains unvalidated. The app disables unavailable DWG downloads and returns an explicit error. Never rename DXF bytes to DWG. Optional ODA File Converter can be configured later with `DUCT_ODA_CONVERTER`; validate an actual output in CAD before claiming readiness.

## Development setup

Python 3.12 is tested. Use the existing checkout; no extra worktree is needed.

```sh
cd /workspace/Duct-sizing-
python -m venv /workspace/.venvs/duct-cad
/workspace/.venvs/duct-cad/bin/python -m pip install -r requirements.txt
python -m venv /workspace/.venvs/administration-cad
/workspace/.venvs/administration-cad/bin/python -m pip install -r projects/administration_rev11/requirements.lock.txt
/workspace/.venvs/administration-cad/bin/python scripts/build_administration.py
/workspace/.venvs/administration-cad/bin/python scripts/validate_administration.py
/workspace/.venvs/administration-cad/bin/python scripts/package_administration.py
/workspace/.venvs/duct-cad/bin/python -m unittest discover -s tests -v
/workspace/.venvs/duct-cad/bin/python app.py --port 5004
```

The development server uses the specified free port; do not stop unrelated processes. Processes must restart in a new cloud task. Internal onboarding HTTP checks do not provide a localhost preview link. No database or credentials are needed.

The wrapper stages a source copy because generators rewrite derived schedules. Run only one rebuild at a time. Failed builds preserve earlier successful outputs. Successful outputs are in ignored `generated/administration/`; packaging writes `generated/delivery/`. Publishing copies validated versioned files into `deliverables/rev11/`. Historical migrations `scripts/prepare_rev10_inputs.py` and `scripts/prepare_rev11_inputs.py` is not part of normal rebuilding; rerunning it replaces proposed route inputs.

Update linked JSON / CSV design inputs together. Excel-only changes are not read by the generator. The generic JSON editor is separate from the Administration source; its constant-size independent routes do not provide these detailed junctions. Portable ZIP rebuilding instructions are in `READ_ME_FIRST.txt`.

## Validation

Independent checks cover delivered CAD exteriors, 11 native dimension lengths, all 85 instrument tags against actual PDF sheet references, 64 airflow-balanced indoor nodes, registered free duct ends, traceable 13 terminal / 20 existing size changes from Rev10, centerline clashes, both DXF audits, 22 color / monochrome A1 sheets, four schematic sheets, 23 workbook tabs, all 116 indoor section velocities / lengths / straight friction values and every headroom envelope. Separate-service insulation footprints do not overlap. All 15 proposed room drops match their branches, and the functional roof main flows match room totals. The legacy bad centerline arrangement is rejected by the validator. OEM assemblies and actual roof geometry are outside the verified scope.

App tests cover generic and project downloads, invalid input and converter failures. Packaging checks ZIP integrity and SHA-256 hashes. Reports describe checks and remaining holds; they do not constitute engineering approval. Native AutoCAD plotting remains unrun.

## Reference

The supplied `D-113391-ADDC-AES-ME-AC-001_REV.1.dwg` is preserved without changes in the source reference directory. Its GNU LibreDWG review conversion required compatibility repairs and enabled layers; it is not an authoritative AutoCAD plot. Reference drawing duties / building geometry were not copied into this design. Bundled reference-vector symbol data is used by normal rebuilds; optional inspection tools under `/workspace/tools/` are not required.

## API

- `GET /api/administration`: revision, source counts and validation report.
- `GET /api/administration/overview`: rebuilt coordination-plan image.
- `GET /api/administration/export/pdf`, `/mono`, `/xlsx`, `/dxf`, `/zip`: current drawings / registers.
- `GET /api/administration/export/dwg`: optional server conversion.
- `GET /api/sample`, `POST /api/preview`, `POST /api/export/dxf`: generic route editor.
