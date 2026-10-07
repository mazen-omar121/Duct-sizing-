ADMINISTRATION HVAC — REVISION 10

START WITH Administration_HVAC_Junction_Review_Rev10.pdf: three actual drawing
sheets D-019 (six junction enlargements), D-020 (crossings / height constraint),
and D-021 (terminal moves / final size changes). Full detailed PDF has 21 A1
sheets; the supplementary functional schematic has four sheets.

Open Administration_HVAC_Detailed_Layout_Rev10.dxf in AutoCAD.
Review layouts D001_A1 through D021_A1, then Save As DWG.
Keep M-MASK enabled. VIEWPORT is non-plotting; text styles use Arial.
Print A1 at actual size / 100% for stated plan scales; do not scale NTS details.
D-019 scales are shown per detail (1:20 / 1:25). Native AutoCAD plotting has not
been run; compare your first plot with the supplied PDF.

Rev10 rebuilds duct connections / route topology. It has 122 section paths,
53 retained terminal duties and 85 retained instrument requirements. Proposed
22 terminal relocations and clear section size changes are documented. Shared
corridor runs are real aggregate-flow headers. No unintended same-service
polygon overlaps / retraced centerlines are permitted. Adapters replace the
original throat; service walls are drawn as one continuous exterior.

20 SUPPLY / RETURN / EXTRACT CROSSINGS REMAIN AS COORDINATION PROPOSALS.
User confirmed structural slab/roof underside 4.000 m. Indoor insulation 50 mm
is an assumption, NOT a verified UAE standard / project specification.
Crossing register calculates maximum local BOD bounds with assumed 100 mm
inter-insulation gap and 100 mm structure/hanger allowance. These values are
NOT assigned connected-network levels. Finished ceiling, beams, access and
supports remain to be coordinated. CX-08 stack (750 mm SA / 800 mm RA) leaves
the lowest insulated surface at +2.050 m under those assumptions: resolve a
shallower section or reroute against the required ceiling / headroom.

Engineering holds also include pressure / outdoor-air balance, selected
fitting K / fan ESP / curves, OEM face-to-face / equipment / terminal
performance, fire boundaries and I&C settings / approved wiring. Toilet net
flow is about -18.69 L/s and kitchen net is zero; neither verifies +25 Pa.
Issue is for engineering coordination; checked / approved identities pending.
See REVISION_10.md and independent_validation.json for exact scope and checks.

To rebuild the source: install source/requirements.txt in Python 3.12, then
run source/cad-package/src/build_engineering_drawings.py, build_schematic.py
and build_registers.py sequentially. Generators rewrite derived schedules;
preserve edited inputs. Do not mix Rev08 / Rev09 / Rev10 inputs.
