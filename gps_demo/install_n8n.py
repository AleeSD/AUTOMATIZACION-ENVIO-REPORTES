"""Instalación local reproducible, sin cambiar PATH ni herramientas de la cuenta."""
import hashlib
import json
import os
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

from .pipeline import ROOT


def main():
    runtime = ROOT / '.runtime'
    downloads = runtime / 'downloads'
    downloads.mkdir(parents=True, exist_ok=True)
    node_home = runtime / 'node24'
    marker = runtime / 'node24-version.json'
    if not marker.exists():
        releases = json.load(urllib.request.urlopen('https://nodejs.org/dist/index.json', timeout=30))
        version = next(r['version'] for r in releases if r['version'].startswith('v24.') and r['lts'] and 'win-x64-zip' in r['files'])
        filename = f'node-{version}-win-x64.zip'
        base = f'https://nodejs.org/dist/{version}/'
        checksums = urllib.request.urlopen(base + 'SHASUMS256.txt', timeout=30).read().decode()
        expected = next(line.split()[0] for line in checksums.splitlines() if line.split()[-1] == filename)
        archive = downloads / filename
        print(f'Descargando Node {version} portable para n8n; PATH de cuenta sin cambios.', flush=True)
        urllib.request.urlretrieve(base + filename, archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
            raise ValueError('La descarga Node no coincide con el SHA-256 oficial')
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                relative = Path(*Path(member.filename).parts[1:])
                target = (node_home / relative).resolve()
                if not target.is_relative_to(node_home.resolve()):
                    raise ValueError('Ruta no válida en archivo portable')
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(bundle.read(member))
        marker.write_text(json.dumps({'version': version, 'sha256': expected}), encoding='utf-8')
    env = os.environ.copy()
    env['PATH'] = str(node_home) + os.pathsep + env['PATH']
    env['npm_config_cache'] = str(runtime / 'npm-cache')
    env['npm_config_prefix'] = str(runtime / 'npm-prefix')
    package = runtime / 'n8n'
    package.mkdir(parents=True, exist_ok=True)
    if (ROOT / 'n8n/package-lock.json').exists():
        for filename in ['package.json', 'package-lock.json']:
            shutil.copyfile(ROOT / 'n8n' / filename, package / filename)
        command = ['ci', '--prefix', str(package), '--no-audit', '--no-fund']
    else:
        command = ['install', '--prefix', str(package), '--save-exact', '--no-audit', '--no-fund', 'n8n@2.43.7']
    subprocess.run([str(node_home / 'npm.cmd'), *command], env=env, check=True, cwd=ROOT)
    print('n8n 2.43.7 instalado localmente con Node 24 portable.', flush=True)


if __name__ == '__main__':
    main()
