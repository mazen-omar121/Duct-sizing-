"""Independently validate, package and copy the separate DX method option."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
import fitz

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'projects/main_duct_and_return'
if not SOURCE.is_dir():
    SOURCE = ROOT / 'source'
OUT = ROOT / 'generated/main_duct_and_return'
DELIVERY = ROOT / 'deliverables/main-duct-and-return'
TITLE = 'Main duct and return'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    subprocess.run([sys.executable, str(ROOT / 'scripts/validate_main_duct_and_return.py')], check=True)
    report = json.loads((OUT / 'validation.json').read_text())
    assert report['detailed_A1_sheets'] == 14 and report['retained_instruments_graphically_checked'] == 85
    assert report['additional_DX_candidates_graphically_checked'] == 22
    review = OUT / (TITLE + ' - Method review.pdf')
    with fitz.open(OUT / (TITLE + '.pdf')) as full, fitz.open() as subset:
        for page in [0, 3, 4]:
            subset.insert_pdf(full, from_page=page, to_page=page)
        subset.save(review)
        page = full[0]
        page.get_pixmap(matrix=fitz.Matrix(1700 / page.rect.width, 1700 / page.rect.width)).save(OUT / (TITLE + ' - Overview.png'))
    files = [TITLE + '.pdf', TITLE + ' - Monochrome.pdf', TITLE + '.dxf',
             TITLE + ' - Registers.xlsx', review.name, TITLE + ' - Overview.png', 'Common_main_sizing.csv',
             'Additional_DX_proposals.csv', 'Instrument_drawing_index.csv',
             'method_basis.json', 'validation.json']
    contents = {name: OUT / name for name in files}
    contents['READ_ME_FIRST.txt'] = SOURCE / 'READ_ME_FIRST.txt'
    contents['README.md'] = SOURCE / 'README.md'
    for path in SOURCE.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            contents['source/' + path.relative_to(SOURCE).as_posix()] = path
    for name in ['validate_main_duct_and_return.py', 'package_main_duct_and_return.py']:
        contents['scripts/' + name] = ROOT / 'scripts' / name
    checksums = {name: digest(path) for name, path in contents.items()}
    archive = OUT / (TITLE + '.zip')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as package:
        for name, path in contents.items():
            package.write(path, name)
        package.writestr('SHA256.json', json.dumps(checksums, indent=2) + '\n')
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None
        for name, expected in checksums.items():
            assert hashlib.sha256(package.read(name)).hexdigest() == expected, name
    DELIVERY.mkdir(parents=True, exist_ok=True)
    for name in files:
        shutil.copyfile(OUT / name, DELIVERY / name)
    for name in ['READ_ME_FIRST.txt', 'README.md']:
        shutil.copyfile(SOURCE / name, DELIVERY / name)
    shutil.copyfile(archive, DELIVERY / archive.name)
    manifest = {name: digest(DELIVERY / name) for name in files + ['READ_ME_FIRST.txt', 'README.md', archive.name]}
    (DELIVERY / 'SHA256.json').write_text(json.dumps(manifest, indent=2) + '\n')
    for name, expected in manifest.items():
        assert digest(DELIVERY / name) == expected, name
    print(json.dumps({'package': str(DELIVERY / archive.name), 'bytes': archive.stat().st_size,
                      'checksum_verified_files': len(contents), 'delivery_manifest_files': len(manifest)}))


if __name__ == '__main__':
    main()
