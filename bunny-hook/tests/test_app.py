from unittest import TestCase
from contextlib import contextmanager
import json

from flask import appcontext_pushed, g
from werkzeug.datastructures import Headers

import env
import api
from api.routes import get_hmac
from test_secrets import TOKENS


class TestAPI(TestCase):

    @classmethod
    def setUpClass(cls):
        '''
        Set up some class-wide attributes for testing.
        '''
        api.app.testing = True
        cls.app = api.app.test_client()
        cls.tokens = TOKENS

        # Good and bad authentication credentials
        cls.good_sig = get_hmac(cls.tokens[0])
        cls.bad_sig = get_hmac('bogus token')

    @contextmanager
    def authenticate(self):
        '''
        Inject fake security tokens into the app context for testing.
        '''
        def handler(sender, **kwargs):
            g.tokens = self.tokens

        with appcontext_pushed.connected_to(handler, api.app):
            yield

    def test_successful_request(self):
        '''
        Test a successful request.
        '''
        post_data = json.dumps({
                'ref': 'refs/head/master',
                'repository': {
                    'name': 'test-repo'
                }
            })

        headers = Headers()
        headers.add('X-Hub-Signature', self.good_sig)

        with self.authenticate():
            post_request = self.app.post('/hooks/github/master',
                                         content_type='application/json',
                                         data=post_data,
                                         headers=headers)

        self.assertEqual(post_request.status_code, 202)

        response = json.loads(post_request.data.decode('utf-8'))
        expected = 'Build started for ref refs/head/master of repo test-repo'
        self.assertEqual(response.get('status'), expected)

    def test_authentication_failed(self):
        '''
        Test a bad request where the secret token doesn't authenticate.
        '''
        post_data = json.dumps({
                'ref': 'refs/head/master',
                'repository': {
                    'name': 'test-repo'
                }
            })

        headers = Headers()
        headers.add('X-Hub-Signature', self.bad_sig)

        with self.authenticate():
            post_request = self.app.post('/hooks/github/master',
                                         content_type='application/json',
                                         data=post_data,
                                         headers=headers)

        self.assertEqual(post_request.status_code, 401)

        response = json.loads(post_request.data.decode('utf-8'))
        expected = 'Request signature failed to authenticate'
        self.assertEqual(response.get('status'), expected)

    def test_incorrect_branch_name(self):
        '''
        When the ref path from GitHub is different from the hook branch name,
        make sure that the app does nothing.
        '''
        post_data = json.dumps({'ref': 'refs/heads/master'})

        headers = Headers()
        headers.add('X-Hub-Signature', self.good_sig)

        with self.authenticate():
            post_request = self.app.post('/hooks/github/deploy',
                                         content_type='application/json',
                                         data=post_data,
                                         headers=headers)

        self.assertEqual(post_request.status_code, 400)

        response = json.loads(post_request.data.decode('utf-8'))
        msg = 'Skipping build for unregistered branch "refs/heads/master"'
        self.assertEqual(response.get('status'), msg)

    def test_no_ref(self):
        '''
        Test a bad request (does not contain the `ref` attribute).
        '''
        post_data = json.dumps({'test': 'test'})

        headers = Headers()
        headers.add('X-Hub-Signature', self.good_sig)

        with self.authenticate():
            post_request = self.app.post('/hooks/github/deploy',
                                         content_type='application/json',
                                         data=post_data,
                                         headers=headers)

        self.assertEqual(post_request.status_code, 400)

        response = json.loads(post_request.data.decode('utf-8'))
        expected = "Malformed request payload: {'test': 'test'}"
        self.assertEqual(response.get('status'), expected)
