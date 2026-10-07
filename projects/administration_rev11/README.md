# Administration HVAC Rev11 CAD source

Read REVISION_11.md and READ_ME_FIRST.txt for the roof-distribution option, 3.30 m ceiling envelope and engineering holds. Option selection and actual roof routing / structural penetrations / OEM selections remain pending.

Use scripts/build_administration.py from the repository root; it stages this source before running generators, which rewrite derived schedules. Portable ZIP: install source/requirements.txt with Python 3.12, then run build_engineering_drawings.py, build_schematic.py and build_registers.py from source/cad-package/src, in order, with source as working directory. Do not rerun prepare_rev11_inputs.py after editing prepared inputs.

Duct_sections.csv: indoor measured paths only. Roof_main_basis.csv: functional common-main flows / sizes, actual routes / levels / lengths TBC. Roof_risers.csv: 15 proposed room drops. Headroom_register.csv: per-section envelope at proposed bare BOD +3.400 m, assumed 50 mm indoor insulation. Rev11 change logs compare against Rev10. Instruments.csv and IO_points.csv retain all requirements.

Review D-019 to D-022, then open the detailed DXF in AutoCAD, inspect D001_A1 through D022_A1 and Save As DWG. Native AutoCAD plotting has not been verified. Engineering coordination only, not for construction.
