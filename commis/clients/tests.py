import datetime

from django.test import TestCase
import chef
from chef.auth import sign_request
from chef.rsa import Key, SSLError

from commis.clients.models import Client
from commis.test import ChefTestCase, TestChefAPI

class ClientTestCase(TestCase):
    def test_create(self):
        c = Client.objects.create(name='test_1')
        self.assertTrue(c.key)
        self.assertTrue(c.key.public_export())
        self.assertTrue(c.key.private_export())

        c2 = Client.objects.get(name='test_1')
        self.assertTrue(c2.key)
        self.assertTrue(c2.key.public_export())
        self.assertRaises(SSLError, c2.key.private_export)


class APITestCase(ChefTestCase):
    def sign_request(self, path, **kwargs):
        d = dict(key=self.api.key, http_method='GET',
            path=self.api.parsed_url.path+path.split('?', 1)[0], body=None,
            host=self.api.parsed_url.netloc, timestamp=datetime.datetime.utcnow(),
            user_id=self.api.client)
        d.update(kwargs)
        auth_headers = sign_request(**d)
        headers = {}
        for key, value in auth_headers.iteritems():
            headers['HTTP_'+key.upper().replace('-', '_')] = value
        return headers

    def test_good(self):
        path = '/clients'
        headers = self.sign_request(path)
        response = self.client.get('/api'+path, **headers)
        self.assertEqual(response.status_code, 200)

    def test_bad_timestamp(self):
        path = '/clients'
        headers = self.sign_request(path, timestamp=datetime.datetime(2000, 1, 1))
        response = self.client.get('/api'+path, **headers)
        self.assertContains(response, 'clock', status_code=401)

    def test_no_timestamp(self):
        path = '/clients'
        headers = self.sign_request(path)
        del headers['HTTP_X_OPS_TIMESTAMP']
        response = self.client.get('/api'+path, **headers)
        self.assertEqual(response.status_code, 401)

    def test_no_sig(self):
        path = '/clients'
        headers = self.sign_request(path)
        for key in headers.keys():
            if key.startswith('HTTP_X_OPS_AUTHORIZATION'):
                del headers[key]
        response = self.client.get('/api'+path, **headers)
        self.assertEqual(response.status_code, 401)

    def test_no_sig2(self):
        path = '/clients'
        headers = self.sign_request(path, key=Key.generate(2048))
        response = self.client.get('/api'+path, **headers)
        self.assertEqual(response.status_code, 401)

    def test_bad_method(self):
        path = '/clients'
        headers = self.sign_request(path, http_method='POST')
        response = self.client.get('/api'+path, **headers)
        self.assertEqual(response.status_code, 401)

    def test_no_userid(self):
        path = '/clients'
        headers = self.sign_request(path)
        del headers['HTTP_X_OPS_USERID']
        response = self.client.get('/api'+path, **headers)
        self.assertEqual(response.status_code, 401)


class ClientAPITestCase(ChefTestCase):
    def test_list(self):
        clients = chef.Client.list()
        self.assertTrue('unittest' in clients)

    def test_list_fail(self):
        api = TestChefAPI(self.client, Key.generate(2048), self._client.name)
        self.assertRaises(chef.ChefError, chef.Client.list, api=api)

    def test_get(self):
        client = chef.Client('unittest')
        self.assertTrue(client.admin)
        self.assertEqual(client.public_key, self.api.key.public_export())
