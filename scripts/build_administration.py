"""Rebuild the Rev09 engineering package in an isolated staging copy, preserving inputs."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'projects' / 'administration_rev09'
DEST = ROOT / 'generated' / 'administration'


def main():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='admin-rebuild-', dir=DEST.parent) as temp:
        stage = Path(temp) / 'package'
        shutil.copytree(SOURCE, stage)
        # The original generators rewrite some CSVs; do so only in this staging copy.
        for script in ('build_engineering_drawings.py', 'build_schematic.py', 'build_registers.py'):
            subprocess.run([sys.executable, str(stage / 'cad-package' / 'src' / script)],
                           cwd=stage, check=True)
        report = json.loads((stage / 'drawing_validation.json').read_text())
        assert report['sheets'] == 18 and report['DXF_audit'] == 'passed'
        assert report['duct_geometry']['valid_section_polygons'] == 114
        assert report['room_terminal_totals'] == 'passed'
        assert report['instrumentation_coverage']['scheduled'] == 85
        assert report['instrumentation_coverage']['missing_tags'] == []
        # Retain an earlier successful build if any generator fails.
        if DEST.exists():
            backup = Path(temp) / 'previous'
            DEST.rename(backup)
            try:
                stage.rename(DEST)
            except BaseException:
                backup.rename(DEST)
                raise
        else:
            stage.rename(DEST)
    print(f'Validated Rev09 outputs: {DEST}')


if __name__ == '__main__':
    main()
