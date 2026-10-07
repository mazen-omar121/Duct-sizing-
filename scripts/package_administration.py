"""Package validated Rev11 drawings, engineering holds and reproducible CAD source."""
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
    assert report['revision']==11 and report['detailed_sheets']==22 and report['instrument_tags']==85
    review=OUT/'Administration_HVAC_Junction_Review_Rev11.pdf'
    with fitz.open(OUT/'Administration_Detailed_HVAC_Duct_Flow_Diagram.pdf') as all_sheets:
        with fitz.open() as subset:
            subset.insert_pdf(all_sheets,from_page=18,to_page=21)
            subset.save(review)
    mappings={
        'Administration_HVAC_Detailed_Layout.dxf':'Administration_HVAC_Detailed_Layout_Rev11.dxf',
        'Administration_Detailed_HVAC_Duct_Flow_Diagram.pdf':'Administration_HVAC_Detailed_Drawings_Rev11.pdf',
        'Administration_Detailed_HVAC_Duct_Flow_Diagram_Monochrome.pdf':'Administration_HVAC_Detailed_Drawings_Rev11_Monochrome.pdf',
        'Administration_HVAC_Junction_Review_Rev11.pdf':'Administration_HVAC_Junction_Review_Rev11.pdf',
        'Administration_HVAC_Drawing_Registers_Rev11.xlsx':'Administration_HVAC_Drawing_Registers_Rev11.xlsx',
        'Administration_HVAC_Schematic.dxf':'Administration_HVAC_Schematic_Rev11.dxf',
        'Administration_HVAC_Schematic.pdf':'Administration_HVAC_Schematic_Rev11.pdf',
        'Administration_HVAC_Overview.png':'Administration_HVAC_Overview_Rev11.png',
        'drawing_validation.json':'drawing_validation.json',
        'independent_validation.json':'independent_validation.json',
    }
    note=(ROOT/'projects/administration_rev11/READ_ME_FIRST.txt').read_text()
    archive=OUT/'Administration_HVAC_Rev11.zip';checksum={}
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for original,renamed in mappings.items():
            p=OUT/original;checksum[renamed]=hashlib.sha256(p.read_bytes()).hexdigest();z.write(p,renamed)
        z.writestr('READ_ME_FIRST.txt',note)
        source=ROOT/'projects/administration_rev11'
        for name in ['REVISION_11.md','README.md']:z.write(source/name,name)
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
    (delivery/'SHA256_Rev11.json').write_text(json.dumps(checksum,indent=2)+'\n')
    (delivery/'READ_ME_FIRST_Rev11.txt').write_text(note)
    print(f'Validated download package: {delivery/archive.name} ({archive.stat().st_size} bytes)')


if __name__=='__main__':main()
