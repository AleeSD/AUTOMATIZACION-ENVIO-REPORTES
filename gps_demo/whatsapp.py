"""Envío supervisado de un documento por empresa; simulación por defecto."""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from openpyxl import load_workbook

from .pipeline import ROOT

MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


class ApiError(Exception):
    """Error sin cuerpos HTTP, credenciales ni encabezados."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class MetaClient:
    def __init__(self, token, phone_id, version):
        if not token or not re.fullmatch(r'\d+', phone_id) or not re.fullmatch(r'v\d+\.0', version):
            raise ValueError('Credenciales Meta incompletas o inválidas')
        self.token = token
        self.base = f'https://graph.facebook.com/{version}/{phone_id}'
        self.opener = build_opener(NoRedirect())

    def post(self, endpoint, body, content_type):
        request = Request(self.base + endpoint, data=body, method='POST', headers={
            'Authorization': 'Bearer ' + self.token, 'Content-Type': content_type})
        try:
            with self.opener.open(request, timeout=30) as response:
                return json.loads(response.read())
        except HTTPError as error:
            code, subcode = None, None
            try:
                details = json.loads(error.read()).get('error', {})
                code, subcode = details.get('code'), details.get('error_subcode')
            except (ValueError, AttributeError):
                pass
            # No propagar mensajes de Meta que puedan repetir datos de entrada.
            code = code if isinstance(code, int) else None
            subcode = subcode if isinstance(subcode, int) else None
            raise ApiError(f'Meta HTTP {error.code}; codigo={code}; subcodigo={subcode}') from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise ApiError('Fallo de red o respuesta no interpretable; revisar estado antes de reintentar') from None

    def upload(self, path):
        mime = 'application/pdf' if path.suffix.lower() == '.pdf' else MIME
        boundary = 'gpsdemo' + uuid.uuid4().hex
        fields = (
            f'--{boundary}\r\nContent-Disposition: form-data; name="messaging_product"\r\n\r\nwhatsapp\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="type"\r\n\r\n{mime}\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\nContent-Type: {mime}\r\n\r\n'
        ).encode()
        result = self.post('/media', fields + path.read_bytes() + f'\r\n--{boundary}--\r\n'.encode(), f'multipart/form-data; boundary={boundary}')
        media_id = result.get('id') if isinstance(result, dict) else None
        if not isinstance(media_id, str) or not media_id:
            raise ApiError('Meta no devolvió identificador de archivo')
        return media_id

    def document(self, phone, media_id, filename, caption):
        payload = {'messaging_product': 'whatsapp', 'recipient_type': 'individual', 'to': phone,
                   'type': 'document', 'document': {'id': media_id, 'filename': filename, 'caption': caption}}
        result = self.post('/messages', json.dumps(payload, ensure_ascii=False).encode(), 'application/json')
        try:
            message_id = result['messages'][0]['id']
        except (KeyError, IndexError, TypeError):
            raise ApiError('Meta no devolvió identificador de mensaje; entrega incierta') from None
        if not isinstance(message_id, str) or not message_id:
            raise ApiError('Identificador de mensaje inválido; entrega incierta')
        return message_id

    def template_document(self, phone, media_id, filename, name, language, parameters):
        components = [{'type': 'header', 'parameters': [{'type': 'document', 'document': {'id': media_id, 'filename': filename}}]}]
        if parameters:
            components.append({'type': 'body', 'parameters': [{'type': 'text', 'text': str(v)} for v in parameters]})
        payload = {'messaging_product': 'whatsapp', 'to': phone, 'type': 'template',
                   'template': {'name': name, 'language': {'code': language}, 'components': components}}
        result = self.post('/messages', json.dumps(payload, ensure_ascii=False).encode(), 'application/json')
        try:
            message_id = result['messages'][0]['id']
        except (KeyError, IndexError, TypeError):
            raise ApiError('Meta no devolvió identificador de plantilla; entrega incierta') from None
        if not isinstance(message_id, str) or not message_id:
            raise ApiError('Identificador de plantilla inválido; entrega incierta')
        return message_id


def latest_batch(root=ROOT):
    config = json.loads((root / 'config/onway.json').read_text(encoding='utf-8'))
    output = (root / config['output']).resolve()
    reference = output / 'ultimo_lote_empresa.json'
    if reference.exists():
        data = json.loads(reference.read_text(encoding='utf-8'))
        folder = (output / data['lote']).resolve()
        if not folder.is_relative_to(output) or not (folder / 'manifest.json').is_file():
            raise ValueError('Referencia de lote inválida')
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        if manifest.get('schema_version') != 2 or manifest.get('fecha') != data['fecha']:
            raise ValueError('Referencia de lote no coincide con el manifiesto')
        return folder
    candidates = []
    for path in (root / config['output'] / config['date']).glob('*/manifest.json'):
        data = json.loads(path.read_text(encoding='utf-8'))
        if data.get('schema_version') == 2 and data.get('tipo_reporte') == 'empresa':
            candidates.append(path)
    if not candidates:
        raise ValueError('Primero generar un lote de reportes por empresa')
    return max(candidates, key=lambda path: path.stat().st_mtime).parent


def plan_batch(folder, root=ROOT, document_format='xlsx'):
    from .onway import routing
    folder = Path(folder).resolve()
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('schema_version') != 2 or manifest.get('tipo_reporte') != 'empresa' or manifest.get('modo') != 'simulation':
        raise ValueError('Solo se aceptan lotes nuevos por empresa generados en simulación')
    date.fromisoformat(manifest['fecha'])
    config = json.loads((root / 'config/onway.json').read_text(encoding='utf-8'))
    entries, _ = routing(config, set(), root)
    recipients = {e['id']: e for e in entries}
    documents = {d['ruc']: d for d in manifest['documentos_empresa']}
    messages = manifest['mensajes']
    if not 1 <= len(messages) <= 3:
        raise ValueError('Seleccionar entre uno y tres reportes de empresa')
    plan, seen = [], set()
    for msg in messages:
        entry = recipients.get(msg['coordinador_id'])
        ruc = msg['empresa_ruc']
        if entry is None or entry['company_rucs'] != [ruc] or ruc in seen:
            raise ValueError('La asignación cambió o el lote contiene una empresa repetida; regenerar')
        seen.add(ruc)
        doc = documents.get(ruc)
        expected_name = f'EMPRESA_{ruc}.xlsx'
        if not re.fullmatch(r'\d{11}', ruc) or not doc or msg['documento'] != expected_name or doc['archivo'] != expected_name:
            raise ValueError('Documento no corresponde a la empresa seleccionada')
        path = (folder / expected_name).resolve()
        if path.parent != folder or not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
            raise ValueError('Documento inexistente, fuera del lote o demasiado grande')
        if hashlib.sha256(path.read_bytes()).hexdigest() != doc['sha256']:
            raise ValueError('Documento modificado después de generar el lote; regenerar')
        if len(msg['texto']) > 1024:
            raise ValueError('Resumen supera el límite de la leyenda del documento')
        book = load_workbook(path, read_only=True, data_only=False)
        try:
            sheet = book['Report Alerts']
            rows = iter(sheet.values)
            headers = next(rows)
            company_col = headers.index('Empresa')
            plate_col = headers.index('Placa/Patente')
            detail = list(rows)
            if any(row[company_col] != doc['empresa'] or row[plate_col] not in doc['placas'] for row in detail):
                raise ValueError('El Excel mezcla placas o empresas no autorizadas')
            if len(detail) != doc['alertas'] or book['Resumen']['A6'].value != doc['alertas']:
                raise ValueError('El Excel no concuerda con el manifiesto')
        finally:
            book.close()
        if document_format == 'pdf':
            pdf = doc.get('pdf', {})
            pdf_name = f'EMPRESA_{ruc}.pdf'
            path = (folder / pdf_name).resolve()
            if pdf.get('archivo') != pdf_name or path.parent != folder or not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
                raise ValueError('Falta el PDF de empresa o no corresponde al lote')
            content = path.read_bytes()
            if not content.startswith(b'%PDF-') or hashlib.sha256(content).hexdigest() != pdf.get('sha256'):
                raise ValueError('PDF inválido o modificado; regenerar el lote')
        elif document_format != 'xlsx':
            raise ValueError('Formato de envío no admitido')
        plan.append({'coordinador_id': entry['id'], 'alias': entry['alias'], 'phone': entry['phone'],
                     'empresa_ruc': ruc, 'empresa': doc['empresa'], 'fecha': manifest['fecha'],
                     'archivo': path, 'alertas': doc['alertas'], 'placas': doc['placas'], 'texto': msg['texto']})
    return plan


def public(item, state):
    return {'coordinador_id': item['coordinador_id'], 'fecha': item['fecha'], 'empresa': item['empresa'], 'numero': '***' + item['phone'][-3:],
            'archivo': item['archivo'].name, 'placas': item['placas'], 'alertas': item['alertas'], 'estado': state}


def dispatch(folder, root=ROOT, send=False, window_confirmed=False, client=None, phone_id=None, template=None, document_format='xlsx'):
    if template and document_format != 'pdf':
        raise ValueError('La plantilla de documento requiere PDF; conservar Excel local')
    plan = plan_batch(folder, root, document_format)
    if not send:
        return [public(item, 'simulado') for item in plan]
    if template:
        if not re.fullmatch(r'[a-z0-9_]{1,512}', template.get('name', '')) or not re.fullmatch(r'[a-z]{2}(?:_[A-Z]{2})?', template.get('language', '')):
            raise ValueError('Nombre o idioma de plantilla inválido')
        if any(key not in {'empresa', 'fecha', 'placas', 'alertas'} for key in template.get('body_parameters', [])):
            raise ValueError('Parámetros de plantilla no admitidos')
    if not window_confirmed and not template:
        raise ValueError('Confirmar respuesta reciente de todos los receptores antes de enviar documentos libres')
    phone_id = phone_id or os.environ.get('META_PHONE_NUMBER_ID', '')
    if not re.fullmatch(r'\d+', phone_id):
        raise ValueError('Falta Phone Number ID')
    client = client or MetaClient(os.environ.get('META_ACCESS_TOKEN', ''), phone_id, os.environ.get('META_GRAPH_VERSION', ''))
    storage = root / '.runtime/whatsapp'
    storage.mkdir(parents=True, exist_ok=True)
    database = sqlite3.connect(storage / 'envios.sqlite', timeout=10)
    database.execute('CREATE TABLE IF NOT EXISTS envios (id TEXT PRIMARY KEY, fecha TEXT, ruc TEXT, estado TEXT, mensaje_id TEXT, error TEXT, actualizado TEXT)')
    results = []
    try:
        for item in plan:
            key = hashlib.sha256(f'{phone_id}|{item["fecha"]}|{item["empresa_ruc"]}|{item["phone"]}'.encode()).hexdigest()
            # Reservar antes de tocar la red para impedir envíos concurrentes.
            with database:
                inserted = database.execute('INSERT OR IGNORE INTO envios VALUES (?,?,?,?,?,?,?)',
                    (key, item['fecha'], item['empresa_ruc'], 'reservado', None, None, datetime.now(timezone.utc).isoformat())).rowcount
            if not inserted:
                previous = database.execute('SELECT estado FROM envios WHERE id=?', (key,)).fetchone()[0]
                results.append(public(item, 'omitido_registro_previo:' + previous))
                continue
            stage = 'subiendo'
            try:
                media_id = client.upload(item['archivo'])
                stage = 'enviando'
                with database:
                    database.execute('UPDATE envios SET estado=? WHERE id=?', (stage, key))
                if template:
                    values = {'empresa': item['empresa'], 'fecha': item['fecha'], 'placas': str(len(item['placas'])), 'alertas': str(item['alertas'])}
                    parameters = [values[key] for key in template.get('body_parameters', [])]
                    message_id = client.template_document(item['phone'], media_id, item['archivo'].name, template['name'], template['language'], parameters)
                else:
                    message_id = client.document(item['phone'], media_id, item['archivo'].name, item['texto'])
                with database:
                    database.execute('UPDATE envios SET estado=?,mensaje_id=?,actualizado=? WHERE id=?',
                        ('aceptado_meta', message_id, datetime.now(timezone.utc).isoformat(), key))
                result = public(item, 'aceptado_meta')
                result['mensaje_id'] = message_id
                results.append(result)
            except (ApiError, OSError) as error:
                state = 'incierto_revisar' if stage == 'enviando' else 'fallo_subida_revisar'
                with database:
                    database.execute('UPDATE envios SET estado=?,error=?,actualizado=? WHERE id=?',
                        (state, str(error) if isinstance(error, ApiError) else 'Error local de archivo; sin reintento automatico', datetime.now(timezone.utc).isoformat(), key))
                result = public(item, state)
                result['error'] = str(error) if isinstance(error, ApiError) else 'Error local de archivo'
                results.append(result)
                break
    finally:
        database.close()
    return results


def main():
    parser = argparse.ArgumentParser(description='Reportes por empresa: simulación o envío supervisado Meta')
    parser.add_argument('--batch', type=Path)
    parser.add_argument('--send', action='store_true')
    parser.add_argument('--window-confirmed', action='store_true')
    args = parser.parse_args()
    try:
        folder = args.batch or latest_batch()
        result = dispatch(folder, send=args.send, window_confirmed=args.window_confirmed)
        print(json.dumps({'lote': str(folder), 'modo': 'envio' if args.send else 'simulation', 'resultados': result,
                          'nota': 'aceptado_meta no confirma entrega; revisar recepción'}, ensure_ascii=False, indent=2))
        if any('revisar' in r['estado'] for r in result):
            parser.exit(2, 'Lote detenido. Revisar el registro local antes de reintentar.\n')
    except (ValueError, OSError, KeyError, sqlite3.Error) as error:
        parser.exit(1, f'Error local: {error}\n')


if __name__ == '__main__':
    main()
