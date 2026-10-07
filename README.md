# Administration HVAC drawing app

The current deliverable is **Rev09**, a revised engineering drawing package based on the uploaded Administration Rev08 source and the supplied D-113391 DWG drafting reference. The generic Duct Studio JSON route editor is also retained.

## What changed in the drawings

- Eighteen detailed A1 sheets, plus four supplementary schematic sheets.
- Terminal neck sizes and flows beside enlarged-plan tags (D-004 to D-006).
- Room AI signal trunks and outdoor pressure-reference annotations (D-007).
- Nine individually tagged extract/basement fan DP and vibration diagrams (D-013).
- Six individually tagged airflow-proof and high-limit heater interfaces (D-014).
- Basement temperature/pressure sensing, feeder energy meter and HPCP/HMI/BMS interfaces (D-015).
- Complete index of all 85 scheduled instruments, with explicit graphical sheet references and retained proposal/OEM statuses (D-016).
- Eleven native CAD dimensions, source coordinate notes and setting-out view (D-017).
- Drawing index, revision scope and engineering coordination notes (D-018).
- Explicit CAD entity/layer lineweights and a monochrome PDF print edition.

See [REVISION_09.md](projects/administration_rev09/REVISION_09.md) for exact changes. Original Rev08 source remains under `projects/administration_rev08/`; its prepared deliverables are retained under ignored `generated/administration_rev08/`.

The 114 duct-section inputs, 53 terminal duties/positions, 85 instrument requirements and I/O allocations are retained. Actual room pressure / transfer-air balance and outdoor-air compliance are unresolved. Toilet net SA-EA is about -18.69 L/s; kitchen net is zero. These do not verify +25 Pa targets. Levels, fitting losses/fan ESP, OEM selections, supports/insulation, access and I&C settings/wiring remain open. This is an engineering coordination issue with checked/approved identities pending.

## AutoCAD workflow

Download the [Rev09 drawing and source ZIP](deliverables/Administration_HVAC_Rev09.zip?raw=true), extract it, and open `Administration_HVAC_Detailed_Layout_Rev09.dxf` in AutoCAD. Review layouts **D001_A1 through D018_A1**, then use **Save As → DWG**. Keep `M-MASK` enabled; `VIEWPORT` is non-plotting. Text styles use Arial. Compare the first CAD plot against the supplied PDF. Native AutoCAD plotting has not been run here.

The published files are in [deliverables/](deliverables/). You can also open the [color drawing PDF](deliverables/Administration_HVAC_Detailed_Drawings_Rev09.pdf), [monochrome drawing PDF](deliverables/Administration_HVAC_Detailed_Drawings_Rev09_Monochrome.pdf) and [Excel registers](deliverables/Administration_HVAC_Drawing_Registers_Rev09.xlsx?raw=true) individually. Select **Download raw file** on GitHub if its preview does not provide the file directly. Local rebuilds create fresh outputs under `generated/delivery/`; publishing a later revision requires explicitly replacing the committed deliverables after validation.

Both color review and monochrome print PDFs are included. Print at 100% / actual size on A1 for the stated plan scales. Do not scale NTS details. The package contains updated registers, validation reports and rebuildable CAD source.

A converter is optional for server-side DWG downloads; AutoCAD users do not need it. If desired, install ODA File Converter separately and set `DUCT_ODA_CONVERTER` to its absolute executable path before starting the app. Its Linux package may require a virtual display and graphical runtime dependencies. An executable on PATH alone does not prove conversion readiness: validate an actual output in CAD. No converter is installed here, and real server-side DWG conversion has not been validated. The UI disables those DWG buttons and returns an explicit error; do not rename DXF to DWG.

## Development setup

Python 3.12 is tested. Use the existing checkout; cloud tasks are isolated and do not require another Git worktree.

```sh
cd /workspace/Duct-sizing-
python -m venv /workspace/.venvs/duct-cad
/workspace/.venvs/duct-cad/bin/python -m pip install -r requirements.txt
python -m venv /workspace/.venvs/administration-cad
/workspace/.venvs/administration-cad/bin/python -m pip install -r projects/administration_rev09/requirements.lock.txt
/workspace/.venvs/administration-cad/bin/python scripts/build_administration.py
/workspace/.venvs/administration-cad/bin/python scripts/validate_administration.py
/workspace/.venvs/administration-cad/bin/python scripts/package_administration.py
/workspace/.venvs/duct-cad/bin/python -m unittest discover -s tests -v
/workspace/.venvs/duct-cad/bin/python app.py --port 5001
```

The server is a development server on port 5001; choose another free port with `--port` if needed. No database or credentials are needed. Live processes must restart in a new task. Onboarding checks use internal HTTP requests and do not provide a localhost web-preview link.

The build wrapper runs the generators in a staging copy, preserving source CSV inputs. A failed generator leaves earlier successful outputs intact. Do not run generators directly in the imported source directories: they rewrite derived schedules. Run only one rebuild at a time. Successful outputs are in ignored `generated/administration/`, and the package/download copies are in `generated/delivery/`. After edits, build, independently validate and package before serving the new deliverable.

The Administration project uses its JSON/CSV design data; edits to the generic JSON route editor do not change these drawings. Excel-only edits are not read by the generator. Update the linked JSON/CSV inputs together. Historical revision migration scripts are retained as reference and are not part of the normal rebuild.

## Validation

Both DXF audits passed. Independent validation checks all 85 instrument tags against their actual PDF sheet references, unchanged Rev08 design inputs, 11 native CAD dimension lengths, nine room signal/reference annotations, 18 detailed and 4 schematic A1 sheets, 15 workbook tabs and 114 recalculated velocities. The monochrome edition has 18 sheets. App tests cover the generic and project downloads, invalid input and converter failures. The packaging step tests ZIP integrity and SHA-256 hashes.

`drawing_validation.json` contains geometric checks; `independent_validation.json` contains delivered-file checks. Neither constitutes engineering approval. Native AutoCAD plotting and server-side DWG conversion remain unrun.

## Reference inspection

The supplied `D-113391-ADDC-AES-ME-AC-001_REV.1.dwg` is preserved under the Rev09 `reference/` directory. Its DWG was read using GNU LibreDWG 0.13.4, pinned commit `e3774bd4020fcfebb68150361db74b8b34d170fe`. The review conversion required incompatible sort tables removed, audit repairs and layers enabled for visual inspection; it is not an authoritative AutoCAD plot. Reference building duties/geometry were not copied into the Administration design. The original reference-vector symbol data remains part of the rebuild inputs.

LibreDWG and plotting tools are optional inspection tools outside the project under `/workspace/tools/`; normal drawing rebuilds use only the pinned Python CAD environment and bundled inputs.

## API

- `GET /api/administration`: project revision, counts and current validation report.
- `GET /api/administration/overview`: coordination-plan image.
- `GET /api/administration/export/pdf`, `/mono`, `/xlsx`, `/dxf`, `/zip`: current downloads.
- `GET /api/administration/export/dwg`: optional server-side conversion.
- `GET /api/sample`, `POST /api/preview`, `POST /api/export/dxf`: generic drawing editor.

Generic coordinates/dimensions are millimetres and flows are L/s. It supports constant-size orthogonal rectangular routes and equipment rectangles; it is separate from the detailed Administration generator. Public deployment requires a production WSGI server and appropriate access/resource controls.
