"""Importar credencial local cifrada por n8n y publicar horario configurado."""
import json
import secrets
import subprocess

from .pipeline import ROOT


def main():
    token_path = ROOT / '.runtime/local-api-token'
    token_path.parent.mkdir(parents=True, exist_ok=True)
    if not token_path.exists():
        token_path.write_text(secrets.token_hex(32), encoding='utf-8')
    bootstrap = ROOT / '.runtime/bootstrap'
    bootstrap.mkdir(parents=True, exist_ok=True)
    secret_file = bootstrap / 'credentials.json'
    credentials = [{'id': 'gpsLocalHeader01', 'name': 'GPS API local', 'type': 'httpHeaderAuth',
                    'data': {'name': 'X-GPS-Token', 'value': token_path.read_text(encoding='utf-8')}}]
    secret_file.write_text(json.dumps(credentials), encoding='utf-8')
    workflow = json.loads((ROOT / 'n8n/daily.workflow.json').read_text(encoding='utf-8'))
    daily = json.loads((ROOT / 'config/daily.json').read_text(encoding='utf-8'))
    hour, minute = daily['hour'], daily['minute']
    if not isinstance(hour, int) or not 0 <= hour <= 23 or not isinstance(minute, int) or not 0 <= minute <= 59:
        raise ValueError('Horario diario inválido')
    for node in workflow['nodes']:
        if node['id'] == 'schedule':
            node['parameters']['rule']['interval'][0]['expression'] = f'0 {minute} {hour} * * *'
    workflow['settings']['timezone'] = daily['timezone']
    workflow_file = bootstrap / 'workflow.json'
    workflow_file.write_text(json.dumps(workflow, ensure_ascii=False, indent=2), encoding='utf-8')
    cli = str(ROOT / 'scripts/n8n_cli.cmd')
    try:
        subprocess.run([cli, 'import:credentials', '--input=' + str(secret_file)], check=True, cwd=ROOT)
    finally:
        secret_file.unlink(missing_ok=True)
    subprocess.run([cli, 'import:workflow', '--input=' + str(workflow_file)], check=True, cwd=ROOT)
    subprocess.run([cli, 'publish:workflow', '--id=OSLogisticsGPS01'], check=True, cwd=ROOT)
    print('Flujo publicado. Reiniciar n8n si estaba abierto para aplicar cambios de horario.')


if __name__ == '__main__':
    main()
