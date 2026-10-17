import json
import os
import threading
import unittest
from http.server import HTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from gps_demo import pipeline


class LocalServerTests(unittest.TestCase):
    def test_auth_route_and_fixed_configuration(self):
        ready = threading.Event()
        servers = []
        token = 'token-local-de-prueba-no-productivo'

        def factory(address, handler):
            self.assertEqual(address[0], '127.0.0.1')
            server = HTTPServer(('127.0.0.1', 0), handler)
            servers.append(server)
            ready.set()
            return server

        with patch.dict(os.environ, {'GPS_LOCAL_TOKEN': token}), patch.object(pipeline, 'HTTPServer', factory), patch.object(pipeline, 'run', return_value=(Path('local'), {'modo': 'simulation'})) as process:
            thread = threading.Thread(target=pipeline.serve, daemon=True)
            thread.start()
            self.assertTrue(ready.wait(5))
            server = servers[0]
            base = f'http://127.0.0.1:{server.server_port}'
            try:
                with self.assertRaises(HTTPError) as error:
                    urlopen(Request(base + '/run', method='POST'), timeout=5)
                self.assertEqual(error.exception.code, 403)
                process.assert_not_called()
                with self.assertRaises(HTTPError) as error:
                    urlopen(Request(base + '/run?input=other.xlsx', headers={'X-GPS-Token': token}, method='POST'), timeout=5)
                self.assertEqual(error.exception.code, 404)
                with urlopen(Request(base + '/run', headers={'X-GPS-Token': token}, method='POST'), timeout=5) as response:
                    self.assertEqual(json.load(response)['modo'], 'simulation')
                process.assert_called_once_with(pipeline.ROOT / 'config/onway.json')
            finally:
                server.shutdown()
                server.server_close()
                thread.join(5)
