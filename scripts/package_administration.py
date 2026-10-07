"""Package the validated Rev09 drawings, registers and reproducible CAD source."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'generated'/'administration'


def main():
    report=json.loads((OUT/'independent_validation.json').read_text())
    assert report['revision']==9 and report['instrument_tags']==85
    mappings={
        'Administration_HVAC_Detailed_Layout.dxf':'Administration_HVAC_Detailed_Layout_Rev09.dxf',
        'Administration_Detailed_HVAC_Duct_Flow_Diagram.pdf':'Administration_HVAC_Detailed_Drawings_Rev09.pdf',
        'Administration_Detailed_HVAC_Duct_Flow_Diagram_Monochrome.pdf':'Administration_HVAC_Detailed_Drawings_Rev09_Monochrome.pdf',
        'Administration_HVAC_Drawing_Registers_Rev09.xlsx':'Administration_HVAC_Drawing_Registers_Rev09.xlsx',
        'Administration_HVAC_Schematic.dxf':'Administration_HVAC_Schematic_Rev09.dxf',
        'Administration_HVAC_Schematic.pdf':'Administration_HVAC_Schematic_Rev09.pdf',
        'drawing_validation.json':'drawing_validation.json',
        'independent_validation.json':'independent_validation.json',
    }
    note='''ADMINISTRATION HVAC — REVISION 09

Open Administration_HVAC_Detailed_Layout_Rev09.dxf in AutoCAD.
Review paper-space layouts D001_A1 through D018_A1 and use Save As to save DWG.
Keep M-MASK enabled. VIEWPORT is a non-plotting layer. Text styles use Arial.
Print A1 PDFs at 100% / actual size to preserve stated plan scales. NTS details
must not be scaled. A monochrome print edition and color review edition are included.
Native AutoCAD plotting has not been run; compare your first plot with the PDF.

This delivery contains revised drawings, not the unchanged Rev08 package.
See REVISION_09.md for exact changes and independent_validation.json for checks.

The package includes all 85 scheduled instrument tags and drawing references,
18 detailed sheets, 4 supplementary schematic sheets, an instrument index,
11 native CAD dimensions, and the revised register workbook.

Engineering holds remain: actual pressure/transfer-air balance and outdoor air,
levels/crossing clearances, selected fitting losses/fan ESP/OEM duties, support
and insulation selections, I&C settings and approved wiring. The toilet net flow
is about -18.69 L/s and kitchen net is zero; these do not verify +25 Pa targets.
This is an engineering coordination issue; checked/approved identities are pending.

To rebuild the source: install source/requirements.txt in Python 3.12, then from
source run python cad-package/src/build_engineering_drawings.py, followed by
python cad-package/src/build_schematic.py and python cad-package/src/build_registers.py.
The included generated source copy rewrites derived schedules during rebuilding.
Preserve your edited inputs before running those generators. Rev08 and Rev09
inputs should not be mixed.
'''
    archive=OUT/'Administration_HVAC_Rev09.zip'
    checksum={}
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for original,renamed in mappings.items():
            p=OUT/original
            checksum[renamed]=hashlib.sha256(p.read_bytes()).hexdigest()
            z.write(p,renamed)
        z.writestr('READ_ME_FIRST.txt',note)
        source=ROOT/'projects'/'administration_rev09'
        z.write(source/'REVISION_09.md','REVISION_09.md')
        z.write(source/'PROVENANCE.json','source/PROVENANCE.json')
        z.write(source/'requirements.lock.txt','source/requirements.txt')
        for p in (OUT/'cad-package').rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                z.write(p,'source/'+p.relative_to(OUT).as_posix())
        for p in (source/'reference').glob('*.dwg'):
            z.write(p,'reference/'+p.name)
        z.writestr('SHA256.json',json.dumps(checksum,indent=2)+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,digest in checksum.items():
            assert hashlib.sha256(z.read(name)).hexdigest()==digest
    delivery=ROOT/'generated'/'delivery'
    delivery.mkdir(exist_ok=True)
    shutil.copyfile(archive,delivery/archive.name)
    for original,renamed in mappings.items():
        shutil.copyfile(OUT/original,delivery/renamed)
    print(f'Validated download package: {delivery/archive.name} ({archive.stat().st_size} bytes)')


if __name__=='__main__':
    main()
