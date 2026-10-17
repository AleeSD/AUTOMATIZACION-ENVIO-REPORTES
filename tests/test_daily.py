import json
import unittest
from datetime import date
from unittest.mock import patch

import test_onway
from gps_demo.daily import ready, run_daily


class DailyTests(unittest.TestCase):
    def setUp(self):
        fixture = test_onway.OnwayTests(methodName='runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.root = fixture.root
        (self.root / 'config').mkdir()
        (self.root / 'config/onway.json').write_text(json.dumps(fixture.config), encoding='utf-8')
        self.daily = {'timezone': 'America/Lima', 'hour': 8, 'minute': 0, 'send': True, 'stable_seconds': 0,
                      'template': {'name': '', 'language': 'es', 'body_parameters': ['empresa', 'fecha', 'placas', 'alertas']}}
        (self.root / 'config/daily.json').write_text(json.dumps(self.daily), encoding='utf-8')
        self.folder = self.root / 'input/15-10-2026'
        self.folder.mkdir()
        fixture.source.rename(self.folder / 'one.xlsx')

    def test_requires_complete_snapshot_and_template_without_network(self):
        result = run_daily(self.root, today=date(2026, 10, 16))
        self.assertEqual(result['estado'], 'esperando_confirmacion_archivos')
        ready('2026-10-15', self.root)
        with patch('gps_demo.whatsapp.MetaClient.post') as network:
            result = run_daily(self.root, today=date(2026, 10, 16))
            self.assertEqual(result['estado'], 'requiere_plantilla_meta')
            self.assertEqual(result['fecha_reporte'], '2026-10-15')
            self.assertEqual(len(result['resultados']), 2)
            network.assert_not_called()

    def test_changed_input_is_blocked(self):
        ready('2026-10-15', self.root)
        path = self.folder / 'one.xlsx'
        path.write_bytes(path.read_bytes() + b'changed')
        self.assertEqual(run_daily(self.root, today=date(2026, 10, 16))['estado'], 'entrada_modificada')

    def test_missing_day_does_not_fall_back_to_old_report(self):
        ready('2026-10-15', self.root)
        self.assertEqual(run_daily(self.root, today=date(2026, 10, 17))['estado'], 'esperando_archivos')

    def test_cached_batch_is_reused(self):
        ready('2026-10-15', self.root)
        result = run_daily(self.root, today=date(2026, 10, 16), force_simulation=True)
        self.assertEqual(result['estado'], 'simulado')
        with patch('gps_demo.daily.run_onway') as generate:
            again = run_daily(self.root, today=date(2026, 10, 16), force_simulation=True)
            self.assertEqual(result['lote'], again['lote'])
            generate.assert_not_called()

    def test_selected_company_missing_blocks_generation(self):
        self.fixture.routing['coordinators'][0]['company_rucs'] = ['20333333333']
        self.fixture.save_routing()
        ready('2026-10-15', self.root)
        self.assertEqual(run_daily(self.root, today=date(2026, 10, 16))['estado'], 'faltan_empresas_seleccionadas')
