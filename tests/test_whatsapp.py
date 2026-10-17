import io
import json
import sqlite3
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from gps_demo.onway import run_onway
from gps_demo.whatsapp import ApiError, MetaClient, dispatch, plan_batch, latest_batch
import test_onway


class WhatsappTests(unittest.TestCase):
    def setUp(self):
        fixture = test_onway.OnwayTests(methodName='runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.root = fixture.root
        (self.root / 'config').mkdir()
        (self.root / 'config/onway.json').write_text(json.dumps(fixture.config), encoding='utf-8')
        self.folder, _ = run_onway(fixture.config_path, root=self.root)
        self.client = Mock()
        self.client.upload.return_value = 'media-id'
        self.client.document.return_value = 'wamid.demo'

    def test_simulation_never_touches_network_or_journal(self):
        result = dispatch(self.folder, root=self.root, client=self.client)
        self.assertEqual(len(result), 2)
        self.assertEqual({r['estado'] for r in result}, {'simulado'})
        self.client.upload.assert_not_called()
        self.assertFalse((self.root / '.runtime').exists())

    def test_window_required(self):
        with self.assertRaises(ValueError):
            dispatch(self.folder, root=self.root, send=True, client=self.client, phone_id='123')
        self.client.upload.assert_not_called()

    def test_one_company_document_per_number_and_idempotence(self):
        result = dispatch(self.folder, root=self.root, send=True, window_confirmed=True, client=self.client, phone_id='123')
        self.assertEqual({r['estado'] for r in result}, {'aceptado_meta'})
        self.assertEqual(self.client.upload.call_count, 2)
        calls = self.client.document.call_args_list
        self.assertEqual(calls[0].args[0], '51900000001')
        self.assertEqual(calls[0].args[2], 'EMPRESA_20111111111.xlsx')
        self.assertEqual(calls[1].args[0], '51900000002')
        self.assertEqual(calls[1].args[2], 'EMPRESA_20222222222.xlsx')
        result = dispatch(self.folder, root=self.root, send=True, window_confirmed=True, client=self.client, phone_id='123')
        self.assertTrue(all(r['estado'].startswith('omitido') for r in result))
        self.assertEqual(self.client.upload.call_count, 2)

    def test_uncertain_send_stops_batch_and_is_not_retried(self):
        self.client.document.side_effect = ApiError('Fallo de red')
        result = dispatch(self.folder, root=self.root, send=True, window_confirmed=True, client=self.client, phone_id='123')
        self.assertEqual([r['estado'] for r in result], ['incierto_revisar'])
        self.assertEqual(self.client.upload.call_count, 1)
        # Segunda ejecución omite el primero y puede procesar el segundo;
        # nunca reintenta el mensaje cuya aceptación es incierta.
        self.client.document.side_effect = None
        dispatch(self.folder, root=self.root, send=True, window_confirmed=True, client=self.client, phone_id='123')
        self.assertEqual(self.client.document.call_count, 2)
        with sqlite3.connect(self.root / '.runtime/whatsapp/envios.sqlite') as database:
            states = {r[0] for r in database.execute('SELECT estado FROM envios')}
        self.assertEqual(states, {'incierto_revisar', 'aceptado_meta'})

    def test_tampered_file_blocks_before_network(self):
        path = self.folder / 'EMPRESA_20111111111.xlsx'
        path.write_bytes(path.read_bytes() + b'tampered')
        with self.assertRaises(ValueError):
            dispatch(self.folder, root=self.root, send=True, window_confirmed=True, client=self.client, phone_id='123')
        self.client.upload.assert_not_called()

    def test_changed_assignment_blocks_before_network(self):
        self.fixture.routing['coordinators'][0]['company_rucs'] = ['20333333333']
        self.fixture.save_routing()
        with self.assertRaises(ValueError):
            plan_batch(self.folder, self.root)

    def test_latest_batch_uses_generated_day_instead_of_fixed_config_day(self):
        next_folder, _ = run_onway(self.fixture.config_path, day='2026-10-16', root=self.root)
        self.assertEqual(latest_batch(self.root), next_folder.resolve())
        result = dispatch(next_folder, root=self.root)
        self.assertEqual(result[0]['fecha'], '2026-10-16')
        reference = self.root / 'reports/ultimo_lote_empresa.json'
        reference.write_text(json.dumps({'fecha': '2026-10-16', 'lote': '../../outside'}))
        with self.assertRaises(ValueError):
            latest_batch(self.root)

    def test_media_upload_and_document_payload(self):
        client = MetaClient('fake-token-only-for-unit-test', '123', 'v25.0')
        path = self.folder / 'EMPRESA_20111111111.xlsx'
        with patch.object(client, 'post', return_value={'id': 'media-id'}) as post:
            self.assertEqual(client.upload(path), 'media-id')
            self.assertEqual(post.call_args.args[0], '/media')
            self.assertIn(path.read_bytes(), post.call_args.args[1])
            self.assertIn(b'name="messaging_product"', post.call_args.args[1])
        with patch.object(client, 'post', return_value={'messages': [{'id': 'wamid.demo'}]}) as post:
            client.document('51900000001', 'media-id', path.name, 'Resumen de Empresa A')
            payload = json.loads(post.call_args.args[1])
            self.assertEqual(payload['type'], 'document')
            self.assertEqual(payload['document']['id'], 'media-id')
            self.assertEqual(payload['document']['filename'], path.name)

    def test_http_error_does_not_disclose_token_or_body(self):
        client = MetaClient('fake-secret-test', '123', 'v25.0')
        body = io.BytesIO(json.dumps({'error': {'code': 190, 'message': 'fake-secret-test'}}).encode())
        client.opener = Mock()
        client.opener.open.side_effect = HTTPError('https://graph.facebook.com', 401, 'error', {}, body)
        with self.assertRaises(ApiError) as caught:
            client.post('/messages', b'{}', 'application/json')
        self.assertIn('190', str(caught.exception))
        self.assertNotIn('fake-secret-test', str(caught.exception))

    def test_template_document_and_dispatch_without_window_override(self):
        template = {'name': 'reporte_gps_empresa', 'language': 'es', 'body_parameters': ['empresa', 'fecha', 'placas', 'alertas']}
        self.client.template_document.return_value = 'wamid.template'
        result = dispatch(self.folder, root=self.root, send=True, client=self.client, phone_id='123', template=template, document_format='pdf')
        self.assertEqual({r['estado'] for r in result}, {'aceptado_meta'})
        self.client.document.assert_not_called()
        self.assertEqual(self.client.template_document.call_args_list[0].args[-1], ['Empresa A', '2026-10-15', '1', '1'])
        client = MetaClient('fake-token', '123', 'v25.0')
        with patch.object(client, 'post', return_value={'messages': [{'id': 'wamid.template'}]}) as post:
            client.template_document('51900000001', 'media-id', 'EMPRESA_20111111111.pdf', template['name'], 'es', ['Empresa A'])
            payload = json.loads(post.call_args.args[1])
            self.assertEqual(payload['type'], 'template')
            self.assertEqual(payload['template']['components'][0]['parameters'][0]['document']['id'], 'media-id')

    def test_template_rejects_excel_before_network(self):
        template = {'name': 'reporte_gps_empresa', 'language': 'es', 'body_parameters': []}
        with self.assertRaises(ValueError):
            dispatch(self.folder, root=self.root, send=True, client=self.client, phone_id='123', template=template)
        self.client.upload.assert_not_called()

    def test_modified_pdf_blocks_before_network(self):
        path = self.folder / 'EMPRESA_20111111111.pdf'
        path.write_bytes(path.read_bytes() + b'changed')
        with self.assertRaises(ValueError):
            dispatch(self.folder, root=self.root, send=True, client=self.client, phone_id='123',
                     template={'name': 'reporte_gps_empresa', 'language': 'es', 'body_parameters': []}, document_format='pdf')
        self.client.upload.assert_not_called()
