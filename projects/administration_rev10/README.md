# Administration HVAC Rev10 CAD source

Read REVISION_10.md and the root repository README for scope and engineering holds.

Normal rebuilds use scripts/build_administration.py from the repository root; it stages this source before running the generators because they rewrite derived schedules. For the portable ZIP, install source/requirements.txt with Python 3.12 and run build_engineering_drawings.py, build_schematic.py and build_registers.py from source/cad-package/src, in that order, with source as the working directory.

Duct_sections.csv and Terminals.csv are the proposed Rev10 route inputs. Rev10_route_changes.csv, Rev10_size_changes.csv and Rev10_terminal_changes.csv record changes from Rev09. Instruments.csv and IO_points.csv retain all 85 instrument requirements and original I/O duties. The four schematic sheets show functional air / control sequences, not scaled routing.

Open the generated detailed-layout DXF in AutoCAD, inspect D001_A1 through D021_A1 and Save As DWG. Review D-019 actual junction enlargements, D-020 crossing / level holds and D-021 proposed size / terminal changes before approval. Native AutoCAD plotting has not been performed in this environment.

The structural underside is 4.000 m (user confirmed). Coordination_basis.json records the assumed 50 mm indoor insulation and clearance allowances. D-020 explicitly flags CX-08: its current stack leaves an insulated underside at +2.050 m; a shallower section or reroute must be resolved against the finished ceiling and access needs. No installed duct BOD is assigned.
