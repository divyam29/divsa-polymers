import re
import unittest
from unittest.mock import MagicMock, patch

from pymongo.errors import ConnectionFailure
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Config


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = 'test-only-secret-0123456789-abcdef-0123456789'
    ADMIN_PASSWORD_HASH = generate_password_hash('test-admin-password', method='pbkdf2:sha256:1000')
    SESSION_COOKIE_SECURE = False
    MONGODB_URI = ''
    EMAIL_HOST = ''


class HighPriorityTests(unittest.TestCase):
    def setUp(self):
        logging_setup = patch('app.configure_logging')
        logging_setup.start()
        self.addCleanup(logging_setup.stop)
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.db = MagicMock()
        self.counts = {}

        def increment(query, update, **kwargs):
            key = query['_id']
            self.counts[key] = self.counts.get(key, 0) + 1
            return {'count': self.counts[key]}

        self.db.admin_login_attempts.find_one_and_update.side_effect = increment
        self.storage = patch('app.utils.security.get_db', return_value=self.db)
        self.storage.start()
        self.addCleanup(self.storage.stop)

    def csrf(self, path):
        html = self.client.get(path).get_data(as_text=True)
        return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)

    def login(self, password='wrong', **kwargs):
        return self.client.post('/admin/login', data={
            'password': password, 'csrf_token': self.csrf('/admin/login'),
        }, **kwargs)

    def test_missing_or_short_secrets_fail_startup(self):
        for secret in (None, '', 'divsa_secret_key'):
            with self.subTest(secret=secret):
                config = type('BadConfig', (TestConfig,), {'SECRET_KEY': secret})
                with self.assertRaisesRegex(RuntimeError, 'SECRET_KEY'):
                    create_app(config)

    def test_missing_plaintext_or_invalid_hash_fails_startup(self):
        for value in (None, 'admin123', 'sha256$salt$bad', 'scrypt:invalid$salt$' + 'a' * 64):
            with self.subTest(value=value):
                config = type('BadConfig', (TestConfig,), {'ADMIN_PASSWORD_HASH': value})
                with self.assertRaisesRegex(RuntimeError, 'ADMIN_PASSWORD_HASH'):
                    create_app(config)

    def test_hash_login_clears_old_session(self):
        with self.client.session_transaction() as session:
            session['untrusted_old_state'] = True
        response = self.login('test-admin-password')
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as session:
            self.assertTrue(session['admin_logged_in'])
            self.assertNotIn('untrusted_old_state', session)

    def test_legacy_password_does_not_authenticate(self):
        self.app.config['ADMIN_PASSWORD'] = 'admin123'
        self.assertEqual(self.login('admin123').status_code, 200)
        with self.client.session_transaction() as session:
            self.assertFalse(session.get('admin_logged_in'))

    def test_login_requires_csrf(self):
        self.assertEqual(self.client.post('/admin/login', data={'password': 'test-admin-password'}).status_code, 400)
        self.db.admin_login_attempts.find_one_and_update.assert_not_called()

    def test_rate_limit_shared_across_sessions_and_apps(self):
        with patch('app.utils.security.time.time', return_value=1800):
            for _ in range(5):
                self.assertEqual(self.login().status_code, 200)
            self.client = create_app(TestConfig).test_client()
            response = self.login('test-admin-password')
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.headers['Retry-After'], '900')
            # A spoofed forwarding header must not bypass the same remote address.
            self.assertEqual(self.login(headers={'X-Forwarded-For': '203.0.113.99'}).status_code, 429)
        with patch('app.utils.security.time.time', return_value=2700):
            self.assertEqual(self.login('test-admin-password').status_code, 302)

    def test_different_remote_address_has_separate_limit(self):
        for _ in range(6):
            self.login()
        self.assertEqual(self.login(environ_overrides={'REMOTE_ADDR': '203.0.113.2'}).status_code, 200)

    def test_unavailable_throttle_fails_closed(self):
        with patch('app.utils.security.get_db', return_value=None):
            self.assertEqual(self.login('test-admin-password').status_code, 503)
        self.db.admin_login_attempts.create_index.side_effect = ConnectionFailure('offline')
        with self.assertLogs(self.app.logger, level='ERROR'):
            self.assertEqual(self.login('test-admin-password').status_code, 503)
        with self.client.session_transaction() as session:
            self.assertFalse(session.get('admin_logged_in'))

    def test_inquiry_validation_message_visible_after_redirect(self):
        response = self.client.post('/submit-inquiry', data={
            'csrf_token': self.csrf('/'), 'name': 'Test', 'email': 'invalid', 'phone': '123',
        }, follow_redirects=True)
        self.assertIn('Error in email', response.get_data(as_text=True))
        self.assertIn('inquiry-message-error', response.get_data(as_text=True))
        self.assertEqual(len(response.history), 1)

    def test_valid_inquiry_saves_once_and_redirects(self):
        with patch('app.routes.main.get_db', return_value=self.db), patch('app.routes.main.send_inquiry_email') as email:
            response = self.client.post('/submit-inquiry', data={
                'csrf_token': self.csrf('/'), 'name': 'Test', 'email': 'test@example.com', 'phone': '9876543210',
            })
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.location.endswith('/thank-you'))
            self.db.inquiries.insert_one.assert_called_once()
            email.assert_called_once()

    def test_missing_csrf_inquiry_does_not_save(self):
        with patch('app.routes.main.get_db', return_value=self.db):
            self.assertEqual(self.client.post('/submit-inquiry', data={'name': 'Test'}).status_code, 400)
            self.db.inquiries.insert_one.assert_not_called()

    def test_page_specific_preloads_and_lazy_images(self):
        pages = {
            '/': 'factory-hero.webp', '/products': 'factory-1.webp',
            '/pvc-garden-pipes': 'pvc-garden.webp', '/pvc-braided-pipes': 'pvc-braided.webp',
            '/pvc-recycled-pipes': 'pvc-recycled.webp', '/pvc-pipes-in-ambala': 'factory-2.webp',
            '/pvc-pipes-in-delhi': 'factory-2.webp', '/pvc-pipes-in-punjab': 'factory-2.webp',
            '/infrastructure': None, '/thank-you': None,
        }
        for path, image in pages.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                urls = re.findall(r'<link rel="preload" as="image" href="([^"]+)"', response.get_data(as_text=True))
                self.assertEqual(urls, ['/static/assets/' + image] if image else [])
                for url in urls:
                    with self.client.get(url) as asset:
                        self.assertEqual(asset.status_code, 200)
        html = self.client.get('/').get_data(as_text=True)
        self.assertIn('<img fetchpriority="high"', html)
        self.assertEqual(html.count('<img loading="lazy"'), 4)


if __name__ == '__main__':
    unittest.main()
