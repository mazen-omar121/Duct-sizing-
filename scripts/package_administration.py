"""Package validated Rev10 drawings, engineering holds and reproducible CAD source."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile
import fitz

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'generated/administration'


def main():
    report=json.loads((OUT/'independent_validation.json').read_text())
    assert report['revision']==10 and report['detailed_sheets']==21 and report['instrument_tags']==85
    review=OUT/'Administration_HVAC_Junction_Review_Rev10.pdf'
    with fitz.open(OUT/'Administration_Detailed_HVAC_Duct_Flow_Diagram.pdf') as all_sheets:
        with fitz.open() as subset:
            subset.insert_pdf(all_sheets,from_page=18,to_page=20)
            subset.save(review)
    mappings={
        'Administration_HVAC_Detailed_Layout.dxf':'Administration_HVAC_Detailed_Layout_Rev10.dxf',
        'Administration_Detailed_HVAC_Duct_Flow_Diagram.pdf':'Administration_HVAC_Detailed_Drawings_Rev10.pdf',
        'Administration_Detailed_HVAC_Duct_Flow_Diagram_Monochrome.pdf':'Administration_HVAC_Detailed_Drawings_Rev10_Monochrome.pdf',
        'Administration_HVAC_Junction_Review_Rev10.pdf':'Administration_HVAC_Junction_Review_Rev10.pdf',
        'Administration_HVAC_Drawing_Registers_Rev10.xlsx':'Administration_HVAC_Drawing_Registers_Rev10.xlsx',
        'Administration_HVAC_Schematic.dxf':'Administration_HVAC_Schematic_Rev10.dxf',
        'Administration_HVAC_Schematic.pdf':'Administration_HVAC_Schematic_Rev10.pdf',
        'Administration_HVAC_Overview.png':'Administration_HVAC_Overview_Rev10.png',
        'drawing_validation.json':'drawing_validation.json',
        'independent_validation.json':'independent_validation.json',
    }
    note='''ADMINISTRATION HVAC — REVISION 10

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
'''
    archive=OUT/'Administration_HVAC_Rev10.zip';checksum={}
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for original,renamed in mappings.items():
            p=OUT/original;checksum[renamed]=hashlib.sha256(p.read_bytes()).hexdigest();z.write(p,renamed)
        z.writestr('READ_ME_FIRST.txt',note)
        source=ROOT/'projects/administration_rev10'
        for name in ['REVISION_10.md','README.md']:z.write(source/name,name)
        z.write(source/'PROVENANCE.json','source/PROVENANCE.json')
        z.write(source/'requirements.lock.txt','source/requirements.txt')
        for p in (OUT/'cad-package').rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:z.write(p,'source/'+p.relative_to(OUT).as_posix())
        for p in (source/'reference').glob('*.dwg'):z.write(p,'reference/'+p.name)
        z.writestr('SHA256.json',json.dumps(checksum,indent=2)+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,digest in checksum.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
    delivery=ROOT/'generated/delivery';delivery.mkdir(exist_ok=True)
    shutil.copyfile(archive,delivery/archive.name)
    for original,renamed in mappings.items():shutil.copyfile(OUT/original,delivery/renamed)
    checksum[archive.name]=hashlib.sha256(archive.read_bytes()).hexdigest()
    (delivery/'SHA256_Rev10.json').write_text(json.dumps(checksum,indent=2)+'\n')
    (delivery/'READ_ME_FIRST_Rev10.txt').write_text(note)
    print(f'Validated download package: {delivery/archive.name} ({archive.stat().st_size} bytes)')


if __name__=='__main__':main()
