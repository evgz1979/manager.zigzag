import http.client
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import threading
import unittest
import urllib.parse
from unittest.mock import patch

import remote_access as auth
import server as manager

spec = importlib.util.spec_from_file_location('password_setup', Path(__file__).resolve().parents[1] / 'scripts/remote_access_password.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)

PASSWORD = 'isolated-test-password-only'
HOST = 'manager.example.test'


class RemoteAccessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name).resolve()
        self.credentials = self.path / 'private/password.json'
        auth.save_password(self.credentials, PASSWORD)
        self.now = 1800000000
        self.gate = auth.PasswordGate(self.credentials, HOST, clock=lambda: self.now)
        self.root = self.path / 'documents'
        self.root.mkdir()
        (self.root / 'private.txt').write_text('PRIVATE-CUSTOMER-DATA')
        self.root_patch = patch.object(manager, 'DATA_ROOT', self.root)
        self.root_patch.start()
        self.servers = []
        self.remote = self.serve(auth.handler_class(manager.ManagerHandler))
        self.remote.password_gate = self.gate
        self.local = self.serve(manager.ManagerHandler)

    def tearDown(self):
        for server in self.servers:
            server.shutdown()
            server.server_close()
        self.root_patch.stop()
        self.temp.cleanup()

    def serve(self, handler):
        server = auth.RemoteHTTPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.servers.append(server)
        return server

    def http(self, route, method='GET', body=None, headers=None, server=None):
        connection = http.client.HTTPConnection('127.0.0.1', (server or self.remote).server_port, timeout=3)
        connection.request(method, route, body, {'Host': HOST, **(headers or {})})
        response = connection.getresponse()
        result = response.status, response.getheaders(), response.read()
        connection.close()
        return result

    def form(self):
        status, headers, body = self.http(auth.LOGIN_PATH)
        self.assertEqual(status, 200)
        token = re.search(rb'name="csrf" value="([^"]+)"', body)[1].decode()
        return token, next(value.split(';')[0] for name, value in headers if name == 'Set-Cookie')

    def login(self, **extra):
        csrf, cookie = self.form()
        fields = {'csrf': csrf, 'password': PASSWORD, 'remember': '1', **extra}
        return self.http(auth.LOGIN_PATH, 'POST', urllib.parse.urlencode(fields), {
            'Cookie': cookie, 'Origin': 'https://' + HOST, 'Content-Type': 'application/x-www-form-urlencoded'})

    def session(self, **extra):
        status, headers, _ = self.login(**extra)
        self.assertEqual(status, 303)
        return next(value.split(';')[0] for name, value in headers if name == 'Set-Cookie' and value.startswith(auth.SESSION_COOKIE + '='))

    def test_local_address_stays_open_and_remote_is_gated(self):
        for route in ('/', '/api/health', '/api/file?path=private.txt'):
            self.assertEqual(self.http(route, server=self.local)[0], 200)
            status, _, body = self.http(route)
            self.assertIn(status, (303, 401))
            self.assertNotIn(b'PRIVATE-CUSTOMER-DATA', body)
            self.assertNotIn(str(self.root).encode(), body)

    def test_all_remote_surfaces_are_closed_before_sign_in(self):
        with patch.object(manager, 'read_tree', side_effect=AssertionError('must not read data')):
            for method in ('GET', 'HEAD'):
                for path in ('/', '/hidden-orders.html', '/app.js', '/remote-access.js', '/api/tree', '/api/file?path=private.txt', '/api/health'):
                    status, headers, body = self.http(path, method)
                    self.assertIn(status, (303, 401))
                    self.assertIn(('CDN-Cache-Control', 'no-store'), headers)
                    if method == 'HEAD':
                        self.assertEqual(body, b'')

    def test_host_and_proxy_headers_never_grant_local_trust(self):
        for headers in ({'Host': 'macmini-m4.local:8765'}, {'Host': '127.0.0.1'},
                        {'X-Forwarded-For': '127.0.0.1', 'CF-Connecting-IP': '192.168.1.2', 'Forwarded': 'for=127.0.0.1'},
                        {'X-Forwarded-Host': 'localhost', 'X-Forwarded-Proto': 'https'}):
            self.assertIn(self.http('/api/health', headers=headers)[0], (401, 421))

    def test_authenticated_get_head_files_and_no_store(self):
        cookie = self.session()
        for method in ('GET', 'HEAD'):
            status, headers, body = self.http('/api/file?path=private.txt', method, headers={'Cookie': cookie})
            self.assertEqual(status, 200)
            self.assertIn(('Cache-Control', 'no-store'), headers)
            self.assertEqual(body, b'PRIVATE-CUSTOMER-DATA' if method == 'GET' else b'')
        status, _, body = self.http('/api/health', headers={'Cookie': cookie})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['root'], str(self.root))

    def test_wrong_password_and_tampered_cookie_do_not_authorize(self):
        status, headers, body = self.login(password='incorrect')
        self.assertEqual(status, 401)
        self.assertNotIn(PASSWORD.encode(), body)
        self.assertFalse(any(value.startswith(auth.SESSION_COOKIE) for name, value in headers if name == 'Set-Cookie'))
        cookie = self.session()
        self.assertEqual(self.http('/api/health', headers={'Cookie': cookie[:-1] + ('0' if cookie[-1] != '0' else '1')})[0], 401)

    def test_cookie_expiry_and_password_rotation_invalidate_session(self):
        cookie = self.session()
        self.now += auth.SESSION_SECONDS + 1
        self.assertEqual(self.http('/api/health', headers={'Cookie': cookie})[0], 401)
        self.now -= auth.SESSION_SECONDS + 1
        replacement = auth.password_document('replacement-test-password')
        self.credentials.write_text(json.dumps(replacement))
        self.assertEqual(self.http('/api/health', headers={'Cookie': cookie})[0], 401)

    def test_session_cookie_security_and_remember_choice(self):
        _, headers, _ = self.login()
        session = next(value for name, value in headers if name == 'Set-Cookie' and value.startswith(auth.SESSION_COOKIE))
        for flag in ('Secure', 'HttpOnly', 'Path=/', 'SameSite=Lax', 'Max-Age=2592000'):
            self.assertIn(flag, session)
        self.assertNotIn('Domain=', session)
        _, headers, _ = self.login(remember='')
        session = next(value for name, value in headers if name == 'Set-Cookie' and value.startswith(auth.SESSION_COOKIE))
        self.assertNotIn('Max-Age', session)

    def test_missing_corrupt_unknown_or_open_credentials_fail_closed(self):
        for mutation in ('missing', 'json', 'version', 'mode', 'symlink'):
            if self.credentials.exists() or self.credentials.is_symlink():
                self.credentials.unlink()
            auth.save_password(self.credentials, PASSWORD)
            if mutation == 'missing': self.credentials.unlink()
            if mutation == 'json': self.credentials.write_text('{broken')
            if mutation == 'version':
                value = json.loads(self.credentials.read_text()); value['version'] = 99; self.credentials.write_text(json.dumps(value))
            if mutation == 'mode': self.credentials.chmod(0o644)
            if mutation == 'symlink':
                other = self.credentials.with_suffix('.real'); self.credentials.rename(other); self.credentials.symlink_to(other)
            self.assertEqual(self.http('/api/health')[0], 503)
            self.assertEqual(self.http(auth.LOGIN_PATH)[0], 503)
            self.assertEqual(self.http('/api/health', server=self.local)[0], 200)

    def test_mutations_require_session_and_exact_https_origin(self):
        reached = []
        def mutation(handler):
            reached.append(True); handler.send_json({'saved': True})
        with patch.object(manager.ManagerHandler, 'do_POST', mutation):
            self.assertEqual(self.http('/api/status', 'POST', '{}')[0], 401)
            cookie = self.session()
            for origin in ('', 'null', 'http://' + HOST, 'https://evil.test'):
                self.assertEqual(self.http('/api/status', 'POST', '{}', {'Cookie': cookie, 'Origin': origin})[0], 403)
            self.assertEqual(reached, [])
            self.assertEqual(self.http('/api/status', 'POST', '{}', {'Cookie': cookie, 'Origin': 'https://' + HOST})[0], 200)
            self.assertEqual(reached, [True])

    def test_login_requires_csrf_cookie_and_origin(self):
        csrf, cookie = self.form()
        body = urllib.parse.urlencode({'csrf': csrf, 'password': PASSWORD})
        base = {'Content-Type': 'application/x-www-form-urlencoded', 'Origin': 'https://' + HOST}
        self.assertEqual(self.http(auth.LOGIN_PATH, 'POST', body, base)[0], 403)
        self.assertEqual(self.http(auth.LOGIN_PATH, 'POST', body, {**base, 'Cookie': cookie, 'Origin': 'https://evil.test'})[0], 403)
        self.now += auth.LOGIN_SECONDS + 1
        self.assertEqual(self.http(auth.LOGIN_PATH, 'POST', body, {**base, 'Cookie': cookie})[0], 403)

    def test_duplicate_fields_and_duplicate_cookies_are_rejected(self):
        csrf, cookie = self.form()
        body = urllib.parse.urlencode({'csrf': csrf, 'password': PASSWORD}) + '&password=other'
        self.assertEqual(self.http(auth.LOGIN_PATH, 'POST', body, {'Cookie': cookie, 'Origin': 'https://' + HOST, 'Content-Type':'application/x-www-form-urlencoded'})[0], 400)
        session = self.session()
        self.assertEqual(self.http('/api/health', headers={'Cookie': session + '; ' + session})[0], 401)

    def test_limiter_is_global_even_if_forwarded_ip_changes(self):
        with patch.object(auth.hashlib, 'pbkdf2_hmac', return_value=b'wrong') as derive:
            for _ in range(10): self.assertEqual(self.login(password='wrong')[0], 401)
            status, headers, _ = self.login(password='wrong')
            self.assertEqual(status, 429)
            self.assertIn(('Retry-After', '60'), headers)
            self.assertEqual(derive.call_count, 10)
            self.now += 61
            self.assertEqual(self.login(password='wrong')[0], 401)

    def test_redirect_is_relative_and_no_password_in_page(self):
        for next_path in ('https://evil.test', '//evil.test', '/\\evil.test', '/\r\nInjected: yes', '/_auth/logout'):
            status, headers, body = self.login(next=next_path)
            self.assertEqual(status, 303)
            self.assertIn(('Location', '/'), headers)
            self.assertNotIn(PASSWORD.encode(), body)
        _, headers, _ = self.login(next='/?path=order#todo')
        self.assertIn(('Location', '/?path=order#todo'), headers)

    def test_logout_requires_csrf_and_clears_device_cookie(self):
        cookie = self.session()
        status, _, body = self.http('/_auth/session', headers={'Cookie': cookie})
        self.assertEqual(status, 200)
        csrf = json.loads(body)['csrf']
        headers = {'Cookie': cookie, 'Origin':'https://' + HOST, 'Content-Type':'application/x-www-form-urlencoded'}
        self.assertEqual(self.http('/_auth/logout', 'POST', 'csrf=wrong', headers)[0], 403)
        status, response, _ = self.http('/_auth/logout', 'POST', urllib.parse.urlencode({'csrf':csrf}), headers)
        self.assertEqual(status, 200)
        self.assertTrue(any('Max-Age=0' in value for name, value in response if name == 'Set-Cookie'))

    def test_remote_helpers_are_injected_only_in_authenticated_html(self):
        self.assertNotIn(b'/remote-access.js', self.http('/', server=self.local)[2])
        status, _, body = self.http('/', headers={'Cookie': self.session()})
        self.assertEqual(status, 200)
        self.assertIn(b'<script src="/remote-access.js"></script>', body)

    def test_config_disabled_by_default_and_remote_bind_is_loopback(self):
        config = self.path / 'manager.ini'
        config.write_text('[server]\nport=8765\n')
        self.assertIsNone(auth.settings(config))
        config.write_text('[server]\nport=8765\n[remote_access]\nenabled=true\npublic_host=manager.example.test\nport=18767\ncredentials_file=' + str(self.credentials))
        with patch.object(auth, 'RemoteHTTPServer') as server:
            auth.start(manager.ManagerHandler, config)
            self.assertEqual(server.call_args.args[0], ('127.0.0.1',18767))
        config.write_text(config.read_text().replace('port=18767','port=8765'))
        with self.assertRaises(ValueError): auth.settings(config)

    def test_password_file_is_private_hashed_and_never_replaced(self):
        document = self.credentials.read_text()
        self.assertNotIn(PASSWORD, document)
        self.assertEqual(self.credentials.stat().st_mode & 0o777, 0o600)
        with self.assertRaises(FileExistsError): auth.save_password(self.credentials, 'another-test-password')
        self.assertEqual(self.credentials.read_text(), document)

    def test_setup_is_loopback_only_and_requires_own_page(self):
        destination = self.path / 'new-private/password.json'
        server = setup.setup_server(destination, port=0)
        self.servers.append(server)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        host = '127.0.0.1:' + str(server.server_port)
        self.assertEqual(server.server_address[0], '127.0.0.1')
        self.assertEqual(self.http('/', server=server)[0], 403)
        status, _, page = self.http('/', headers={'Host':host}, server=server)
        csrf = re.search(rb'name="csrf" value="([^"]+)"', page)[1].decode()
        fields = {'csrf':csrf, 'password':PASSWORD, 'confirmation':PASSWORD}
        headers = {'Host':host,'Content-Type':'application/x-www-form-urlencoded','Origin':'http://' + host}
        self.assertEqual(self.http('/', 'POST', urllib.parse.urlencode(fields), {**headers,'Origin':'https://evil.test'}, server=server)[0],403)
        self.assertFalse(destination.exists())
        self.assertEqual(self.http('/', 'POST', urllib.parse.urlencode(fields), headers, server=server)[0],200)
        self.assertTrue(server.setup_done.is_set())
        self.assertNotIn(PASSWORD, destination.read_text())
        self.assertEqual(self.http('/', 'POST', urllib.parse.urlencode(fields), headers, server=server)[0],400)


if __name__ == '__main__':
    unittest.main()
