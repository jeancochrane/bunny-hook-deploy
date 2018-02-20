from unittest import TestCase

import env
from api.payload import Payload


class TestPayload(TestCase):

    def setUp(self):
        self.json = {
            'ref': 'refs/head/master',
            'repository': {
                'name': 'bunny-hook'
            },
            'clone_url': 'https://github.com/jeancochrane/bunny-hook.git'
        }

        self.payload = Payload(self.json)

    def test_payload_validate(self):
        self.assertTrue(self.payload.validate('master'))
        self.assertFalse(self.payload.validate('foo'))

    def test_payload_get(self):
        self.assertEqual(self.payload.get('clone_url'),
                        'https://github.com/jeancochrane/bunny-hook.git')
        self.assertIsNone(self.payload.get('foo'))

    def test_payload_as_dict(self):
        self.assertEqual(self.payload.as_dict, self.json)

    def test_payload_get_branch(self):
        self.assertEqual(self.payload.get_branch(), 'master')

    def test_payload_get_origin(self):
        self.assertEqual(self.payload.get_origin(),
                         'https://github.com/jeancochrane/bunny-hook.git')

    def test_payload_get_name(self):
        self.assertEqual(self.payload.get_name(), 'bunny-hook')

