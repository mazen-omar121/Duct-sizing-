# Administration HVAC drawing app

The current delivery is **Rev10**, which revises the rejected Rev09 duct routing and connections against the supplied CAD examples. It contains 21 detailed A1 drawing sheets, four functional schematic sheets, editable DXF, Excel registers and reproducible CAD source.

Download the [complete Rev10 ZIP](deliverables/rev10/Administration_HVAC_Rev10.zip?raw=true). Start with the [three-page junction / crossing / revision review](deliverables/rev10/Administration_HVAC_Junction_Review_Rev10.pdf): D-019 shows six enlargements of the actual delivered junction geometry, D-020 records crossing constraints, and D-021 records terminal and size changes. The [full color drawings](deliverables/rev10/Administration_HVAC_Detailed_Drawings_Rev10.pdf), [monochrome print edition](deliverables/rev10/Administration_HVAC_Detailed_Drawings_Rev10_Monochrome.pdf) and [Excel registers](deliverables/rev10/Administration_HVAC_Drawing_Registers_Rev10.xlsx?raw=true) are also available individually. On GitHub select **Download raw file** if needed.

## What changed

- One continuous exterior per connected service; later runout fills cannot erase header walls. Adapters replace the constant-width throat and formed fitting radii are part of the actual envelope.
- Corridor distribution / collection uses aggregate-flow headers instead of overlapping individual runouts. Operator returns follow a perimeter tree; meeting, telecom, toilet, bed-room and clean-agent routes are revised.
- Geometry rejects unintended same-service polygon intersections, duplicated / retraced centerlines and unconnected centerline crossings. Every registered joint conserves airflow.
- 122 scheduled section paths, 53 retained terminal duties and 85 instrument requirements. Room duties, terminal neck / face sizes and I/O allocations are retained; 22 terminal relocations and clear section size changes are documented against Rev09.
- Device glyph cores use the supplied reference-vector geometry; straight device stations exclude junctions / crossing footprints. Leadered labels are separated. Actual OEM face-to-face dimensions / actuator access remain to be confirmed.
- Existing individually tagged fan / heater / basement / metering diagrams, complete instrument index and 11 native CAD dimensions are retained and synchronized.

See [REVISION_10.md](projects/administration_rev10/REVISION_10.md). Original Rev08 and published Rev09 source and deliverables remain intact.

## Height and engineering coordination

The user confirmed **4.000 m structural slab/roof underside**; the AFFL datum needs site verification. External indoor insulation is assumed at **50 mm** for coordination, not a verified UAE average or project specification. The crossing register calculates maximum local BOD bounds with assumed 100 mm inter-insulation gap and 100 mm structure / hanger allowance. These values are **not assigned connected-network duct elevations**.

There are **20 separate-service crossings** marked with continuous upper edges and dashed lower edges. At **CX-08**, 750 mm supply and 800 mm return depths require a 1950 mm stack under those assumptions, leaving the lowest insulated surface at **+2.050 m**. Resolve a shallower section or reroute against the required finished ceiling / working access before construction. Finished ceiling, BODs, beams, supports, terminal plenums and selected insulation remain unapproved.

Pressure / outdoor-air balance, selected fitting losses / fan ESP / curves, OEM duties, diffuser performance, fire boundaries and I&C settings / wiring remain open. Toilet net flow is about -18.69 L/s and kitchen net is zero; neither verifies +25 Pa. This is an engineering coordination issue with checked / approved identities pending.

## AutoCAD workflow

Extract the ZIP and open `Administration_HVAC_Detailed_Layout_Rev10.dxf` in AutoCAD. Review **D001_A1 through D021_A1**, then **Save As → DWG**. Keep `M-MASK` enabled; `VIEWPORT` is non-plotting. Text uses Arial. Print A1 PDFs at 100% / actual size for stated scales; D-019 shows each detail's 1:20 or 1:25 scale. NTS details must not be scaled. Native AutoCAD plotting has not been run here; compare the first plot against the supplied PDF.

A server converter is optional for server-side DWG downloads; it is not needed when you use AutoCAD. No converter is installed and direct server DWG generation remains unvalidated. The app disables unavailable DWG downloads and returns an explicit error. Never rename DXF bytes to DWG. Optional ODA File Converter can be configured later with `DUCT_ODA_CONVERTER`; validate an actual output in CAD before claiming readiness.

## Development setup

Python 3.12 is tested. Use the existing checkout; no extra worktree is needed.

```sh
cd /workspace/Duct-sizing-
python -m venv /workspace/.venvs/duct-cad
/workspace/.venvs/duct-cad/bin/python -m pip install -r requirements.txt
python -m venv /workspace/.venvs/administration-cad
/workspace/.venvs/administration-cad/bin/python -m pip install -r projects/administration_rev10/requirements.lock.txt
/workspace/.venvs/administration-cad/bin/python scripts/build_administration.py
/workspace/.venvs/administration-cad/bin/python scripts/validate_administration.py
/workspace/.venvs/administration-cad/bin/python scripts/package_administration.py
/workspace/.venvs/duct-cad/bin/python -m unittest discover -s tests -v
/workspace/.venvs/duct-cad/bin/python app.py --port 5003
```

The development server uses the specified free port; do not stop unrelated processes. Processes must restart in a new cloud task. Internal onboarding HTTP checks do not provide a localhost preview link. No database or credentials are needed.

The wrapper stages a source copy because generators rewrite derived schedules. Run only one rebuild at a time. Failed builds preserve earlier successful outputs. Successful outputs are in ignored `generated/administration/`; packaging writes `generated/delivery/`. Publishing copies validated versioned files into `deliverables/rev10/`. Historical migration `scripts/prepare_rev10_inputs.py` is not part of normal rebuilding; rerunning it replaces proposed route inputs.

Update linked JSON / CSV design inputs together. Excel-only changes are not read by the generator. The generic JSON editor is separate from the Administration source; its constant-size independent routes do not provide these detailed junctions. Portable ZIP rebuilding instructions are in `READ_ME_FIRST.txt`.

## Validation

Independent checks cover delivered CAD exteriors, native dimension lengths, 85 instrument tags against actual PDF sheet references, airflow conservation, traceable terminal / size changes, centerline clashes, both DXF audits, 21 color / monochrome A1 sheets, four schematic sheets, 20 workbook tabs, and all 122 section velocities / lengths / straight-duct friction calculations. The legacy bad centerline arrangement is rejected by the new check. Crossing stack calculations are independently recomputed, including the CX-08 hold.

App tests cover generic and project downloads, invalid input and converter failures. Packaging checks ZIP integrity and SHA-256 hashes. Reports describe checks and remaining holds; they do not constitute engineering approval. Native AutoCAD plotting remains unrun.

## Reference

The supplied `D-113391-ADDC-AES-ME-AC-001_REV.1.dwg` is preserved without changes in the source reference directory. Its GNU LibreDWG review conversion required compatibility repairs and enabled layers; it is not an authoritative AutoCAD plot. Reference drawing duties / building geometry were not copied into this design. Bundled reference-vector symbol data is used by normal rebuilds; optional inspection tools under `/workspace/tools/` are not required.

## API

- `GET /api/administration`: revision, source counts and validation report.
- `GET /api/administration/overview`: rebuilt coordination-plan image.
- `GET /api/administration/export/pdf`, `/mono`, `/xlsx`, `/dxf`, `/zip`: current drawings / registers.
- `GET /api/administration/export/dwg`: optional server conversion.
- `GET /api/sample`, `POST /api/preview`, `POST /api/export/dxf`: generic route editor.
