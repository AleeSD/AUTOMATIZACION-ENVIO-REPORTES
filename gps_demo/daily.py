"""Procesamiento del día anterior, control de lote completo y envío por plantilla."""
import argparse
import hashlib
import hmac
import json
import os
import time
import uuid
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

from .onway import prepare, run_onway, routing
from .pipeline import ROOT
from .whatsapp import dispatch, MetaClient


def settings(root=ROOT):
    return json.loads((root / 'config/onway.json').read_text(encoding='utf-8')), json.loads((root / 'config/daily.json').read_text(encoding='utf-8'))


def input_folder(day, root=ROOT):
    config, _ = settings(root)
    base = root / config['input']
    target = date.fromisoformat(day)
    candidates = [base / target.isoformat(), base / target.strftime('%d-%m-%Y')]
    found = [p for p in candidates if p.is_dir()]
    if not found:
        raise FileNotFoundError('Aún no existe la carpeta de reportes del día anterior')
    if len(found) != 1:
        raise ValueError('Debe existir una única carpeta del día en REPORTES ONWAY, AAAA-MM-DD o DD-MM-AAAA')
    return found[0]


def snapshot(folder, stable_seconds):
    result = []
    for path in sorted(folder.rglob('*')):
        if path.suffix.lower() not in {'.xlsx', '.csv'} or path.name.startswith('~$'):
            continue
        before = path.stat()
        if time.time() - before.st_mtime < stable_seconds or before.st_size > 10 * 1024 * 1024:
            raise ValueError('Archivo demasiado reciente o supera 10 MB: ' + path.name)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError('Archivo cambió durante la lectura: ' + path.name)
        result.append({'archivo': str(path.relative_to(folder)), 'sha256': digest, 'bytes': after.st_size})
    if not result:
        raise ValueError('Carpeta sin reportes')
    return result


def ready(day, root=ROOT):
    config, daily = settings(root)
    folder = input_folder(day, root)
    captured = snapshot(folder, daily['stable_seconds'])
    validation = dict(config, input=str(folder))
    prepare(validation, day, root)
    if snapshot(folder, daily['stable_seconds']) != captured:
        raise ValueError('Los archivos cambiaron durante la validación')
    marker = {'fecha': day, 'archivos': captured, 'confirmado': datetime.now(ZoneInfo('America/Lima')).isoformat()}
    (folder / '_LISTO.json').write_text(json.dumps(marker, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'estado': 'entrada_lista', 'fecha': day, 'archivos': len(captured)}


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name('.' + path.name + uuid.uuid4().hex)
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


def run_daily(root=ROOT, today=None, force_simulation=False):
    config, daily = settings(root)
    today = today or datetime.now(ZoneInfo(daily['timezone'])).date()
    day = (today - timedelta(days=1)).isoformat()
    state_path = root / '.runtime/daily' / (day + '.json')
    def finish(status, **extra):
        result = {'estado': status, 'fecha_reporte': day, 'actualizado': datetime.now(ZoneInfo('America/Lima')).isoformat(), **extra}
        atomic(root / 'outputs/ESTADO_AUTOMATIZACION.json', result)
        return result
    try:
        try:
            folder = input_folder(day, root)
        except FileNotFoundError as error:
            return finish('esperando_archivos', detalle=str(error))
        marker_path = folder / '_LISTO.json'
        if not marker_path.exists():
            return finish('esperando_confirmacion_archivos', detalle='Completar copia y ejecutar marcar_reportes_listos.cmd')
        marker = json.loads(marker_path.read_text(encoding='utf-8'))
        captured = snapshot(folder, daily['stable_seconds'])
        if marker.get('fecha') != day or marker.get('archivos') != captured:
            return finish('entrada_modificada', detalle='Volver a confirmar los archivos del día después de terminar la copia')
        fingerprint = hashlib.sha256(json.dumps(captured, sort_keys=True).encode()).hexdigest()
        _, exported, _ = prepare(dict(config, input=str(folder)), day, root)
        entries, _ = routing(config, set(exported._ruc), root)
        selected = {r for e in entries for r in e['company_rucs']}
        if not selected or not selected.issubset(set(exported._ruc)):
            return finish('faltan_empresas_seleccionadas', detalle='Faltan exportaciones para una o más empresas del piloto')
        cached = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
        routing_hash = hashlib.sha256((root / config['routing']).read_bytes()).hexdigest()
        config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
        if (cached.get('fingerprint'), cached.get('routing_hash'), cached.get('config_hash')) == (fingerprint, routing_hash, config_hash) and (root / cached.get('lote', '') / 'manifest.json').is_file():
            batch = root / cached['lote']
        else:
            batch, _ = run_onway(root / 'config/onway.json', day=day, root=root, source_dir=folder)
            atomic(state_path, {'fingerprint': fingerprint, 'routing_hash': routing_hash, 'config_hash': config_hash, 'lote': str(batch.relative_to(root))})
        # Comprobar otra vez antes de cualquier petición externa.
        if snapshot(folder, daily['stable_seconds']) != captured:
            return finish('entrada_modificada', detalle='Los archivos cambiaron durante la generación')
        preview = dispatch(batch, root=root, document_format='pdf')
        if force_simulation or not daily['send']:
            return finish('simulado', lote=str(batch.relative_to(root)), resultados=preview)
        template = daily['template']
        if not template.get('name'):
            return finish('requiere_plantilla_meta', lote=str(batch.relative_to(root)), resultados=preview,
                          detalle='Configurar el nombre e idioma de la plantilla aprobada con encabezado Documento')
        from .secrets_local import meta_settings
        token, phone_id, version = meta_settings(root)
        client = MetaClient(token, phone_id, version)
        result = dispatch(batch, root=root, send=True, client=client, phone_id=phone_id, template=template, document_format='pdf')
        status = 'requiere_revision_envio' if any('revisar' in item['estado'] for item in result) else 'procesado'
        return finish(status, lote=str(batch.relative_to(root)), resultados=result)
    except (ValueError, OSError, KeyError) as error:
        # Los errores locales no incluyen credenciales ni cuerpos de Meta.
        return finish('requiere_revision_entrada', detalle=str(error))


def serve():
    token_file = ROOT / '.runtime/local-api-token'
    token = token_file.read_text(encoding='utf-8').strip()
    if len(token) < 24:
        raise ValueError('Falta secreto local de integración')
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/health':
                self.reply({'service': 'gps-daily', 'status': 'ok'})
            else:
                self.send_error(404)
        def do_POST(self):
            if self.path not in {'/daily', '/daily-simulate'}:
                self.send_error(404)
                return
            if not hmac.compare_digest(self.headers.get('X-GPS-Token', ''), token):
                self.send_error(403)
                return
            self.close_connection = True
            self.reply(run_daily(force_simulation=self.path == '/daily-simulate'))
        def reply(self, result):
            body = json.dumps(result, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *args):
            pass
    HTTPServer(('127.0.0.1', 8766), Handler).serve_forever()


def main():
    parser = argparse.ArgumentParser(description='Automatización local GPS por empresa')
    parser.add_argument('command', choices=['ready', 'run', 'simulate', 'serve'])
    parser.add_argument('--date')
    args = parser.parse_args()
    if args.command == 'serve':
        serve()
    elif args.command == 'ready':
        if not args.date:
            parser.error('ready requiere --date AAAA-MM-DD')
        print(json.dumps(ready(args.date), ensure_ascii=False))
    else:
        print(json.dumps(run_daily(force_simulation=args.command == 'simulate'), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
