from types import SimpleNamespace
from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase, RequestFactory, Client

from src.entities.branch.models import Branch
from src.entities.user.models import User
from src.middlewares.register_rate_limit import RegisterRateLimitMiddleware
from src.services.hash.bcrypt_hasher import BcryptHashService


class RegisterStateTests(TestCase):
    def register(self, **extra):
        return self.client.post('/register', {
            'name': 'New User', 'email': 'new@example.test', 'password': 'Register-password!', **extra,
        }, content_type='application/json')

    def test_default_state_and_hash(self):
        response = self.register()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content, b'')
        user = User.objects.get(email='new@example.test')
        self.assertFalse(user.is_active)
        self.assertIsNone(user.role)
        self.assertIsNone(user.itec_user)
        self.assertFalse(user.branches.exists())
        self.assertNotEqual(user.password, 'Register-password!')
        self.assertTrue(BcryptHashService().verify('Register-password!', user.password))
        self.assertEqual(user.password.split('$')[2], '12')

    def test_validation_does_not_hash_or_write(self):
        with patch.object(BcryptHashService, 'hash') as hasher:
            response = self.register(password='short')
        self.assertEqual(response.status_code, 400)
        hasher.assert_not_called()
        self.assertFalse(User.objects.exists())

    def test_email_conflict_precedes_itec_and_hash(self):
        User.objects.create(name='Email', email='new@example.test', password='old')
        User.objects.create(name='Itec', email='itec@example.test', password='old', itec_user=12)
        before = list(User.objects.order_by('id').values())
        with patch.object(BcryptHashService, 'hash') as hasher:
            response = self.register(itecUser=12)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['name'], 'UserEmailAlreadyExists')
        hasher.assert_not_called()
        self.assertEqual(list(User.objects.order_by('id').values()), before)

    def test_itec_conflict_does_not_hash_or_write(self):
        User.objects.create(name='Itec', email='itec@example.test', password='old', itec_user=12)
        with patch.object(BcryptHashService, 'hash') as hasher:
            response = self.register(itecUser=12.5)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['name'], 'UserItecAlreadyExists')
        hasher.assert_not_called()
        self.assertEqual(User.objects.count(), 1)

    def test_explicit_fields_and_branch_connections_are_preserved(self):
        branch = Branch.objects.create(id=101, name='Branch', city='Fortaleza', uf='CE', address='Test')
        response = self.register(role='BRANCH', isActive=True, itecUser=15.9,
                                 branches={'connect': [{'id': branch.id}, {'id': branch.id}]})
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email='new@example.test')
        self.assertEqual(user.role, 'BRANCH')
        self.assertTrue(user.is_active)
        self.assertEqual(user.itec_user, 15)
        self.assertEqual(list(user.branches.values_list('id', flat=True)), [101])

    def test_rate_limit_counts_validation_and_success_before_blocking(self):
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.register().status_code, 409)
        self.assertEqual(self.register(password='short').status_code, 400)
        response = self.register(email='blocked@example.test')
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()['name'], 'UserMaxRegisterExceededError')
        self.assertFalse(User.objects.filter(email='blocked@example.test').exists())

    def test_six_utf16_units_and_bcrypt_long_password(self):
        for index, password in enumerate(('😀😀😀', 'A' * 100)):
            response = self.register(email=f'length{index}@example.test', password=password)
            self.assertEqual(response.status_code, 201)
            user = User.objects.get(email=f'length{index}@example.test')
            self.assertTrue(BcryptHashService().verify(password, user.password))

    def test_persistence_failures_do_not_leave_users_or_connections(self):
        branch = Branch.objects.create(id=101, name='Branch', city='Fortaleza', uf='CE', address='Test')
        for extra in ({'role': 'UNKNOWN'}, {'isActive': 'true'}, {'unknownField': True},
                      {'branches': {'connect': [{'id': branch.id}, {'id': 999999}]}}):
            with self.subTest(extra=extra):
                self.client = Client()
                response = self.register(**extra)
                self.assertEqual(response.status_code, 500)
                self.assertEqual(response.json(), {
                    "name": "PersistenceError",
                    "message": "Erro interno, por favor tente novamente mais tarde ou contate o suporte.",
                })
                self.assertFalse(User.objects.exists())
                self.assertFalse(User.branches.through.objects.exists())
                self.assertEqual(Branch.objects.count(), 1)

    def test_zero_unique_violation_preserves_existing_user(self):
        User.objects.create(name='Existing', email='existing@example.test', password='old', itec_user=0)
        before = list(User.objects.values())
        response = self.register(itecUser=0)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["name"], "PersistenceError")
        self.assertEqual(list(User.objects.values()), before)


class RegisterRateLimitTests(TestCase):
    def setUp(self):
        self.middleware = RegisterRateLimitMiddleware(lambda request: HttpResponse(status=201))
        self.factory = RequestFactory()

    def attempt(self, address, now):
        request = self.factory.post('/register', HTTP_X_FORWARDED_FOR=address)
        request.resolver_match = SimpleNamespace(url_name='register')
        with patch('src.middlewares.login_rate_limit.time.time', return_value=now):
            response = self.middleware.process_view(request, None, (), {})
            if response is None:
                response = HttpResponse(status=201)
            return self.middleware.process_response(request, response)

    def test_window_expires_and_successes_count(self):
        for index in range(3):
            response = self.attempt('192.0.2.1', 1000)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response['X-RateLimit-Remaining'], str(2-index))
        self.assertEqual(self.attempt('192.0.2.1', 1599).status_code, 429)
        self.assertEqual(self.attempt('192.0.2.1', 1600).status_code, 201)

    def test_ipv6_subnet_and_rightmost_forwarded_address(self):
        for _ in range(3):
            self.assertEqual(self.attempt('192.0.2.1, 2001:db8:1234:5600::1', 1000).status_code, 201)
        self.assertEqual(self.attempt('192.0.2.2, 2001:db8:1234:56ff::2', 1000).status_code, 429)
        self.assertEqual(self.attempt('192.0.2.1, 2001:db8:1234:5700::1', 1000).status_code, 201)
