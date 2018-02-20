from unittest import TestCase
from unittest.mock import patch
import io
import os
import sys
import shutil

import env
from api.worker import Worker
from decorators import mock_scripts


class MockLogger(object):
    '''
    Redirect logging output so that we can check what gets logged.
    '''
    messages = []

    def __call__(self, message):
        self.messages.append(message)


class TestIntegration(TestCase):
    '''
    Test integrations between different parts of the app.

    To run builds, this test suite uses a special repo, jeancochrane/bunny-hook-test,
    that includes the bare minimum components that are necessary for running a
    build.
    '''
    def setUp(self):
        payload = {
            'ref': 'refs/head/master',
            'repository': {
                'name': 'bunny-hook-test'
            },
            'clone_url': 'https://github.com/jeancochrane/bunny-hook-test.git'
        }

        self.worker = Worker(payload)

    @mock_scripts
    def test_deploy(self):
        '''
        Using this repo as an example, actually run the `deploy` code.

        Mock out Worker.run_scripts, so that we don't run any actual deploy scripts.
        '''
        # Clone the repo as a subdirectory in the tests repo, so that we can
        # clean it up easily
        with patch('logging.info', new_callable=MockLogger) as output:
            self.worker.deploy(tmp_path='./bunny-hook-test')

        expected = [
            'Deploying bunny-hook-test',
            'Cloning https://github.com/jeancochrane/bunny-hook-test.git into ./bunny-hook-test...',
            'Loading config file from ./bunny-hook-test/deploy.yml...',
            'Moving repo from ./bunny-hook-test to ./bunny-hook-test/...',
            'Running prebuild script ./bunny-hook-test/scripts/prebuild.sh...',
            'Running build script ./bunny-hook-test/scripts/build.sh...',
            'Running deployment script ./bunny-hook-test/scripts/deploy.sh...',
            'Finished deploying bunny-hook-test!',
            '---------------------'
        ]

        self.assertEqual(output.messages, expected)

        # Assert repo exists in build location
        self.assertTrue(os.path.exists('bunny-hook-test'))

        # Remove new repo
        shutil.rmtree('bunny-hook-test')

    @mock_scripts
    def test_deploy_twice(self):
        '''
        Make sure the worker can deploy when a tmp directory already exists.
        '''
        # Deploy once
        self.worker.deploy(tmp_path='./bunny-hook-test')

        # Deploy twice
        self.worker.deploy(tmp_path='./bunny-hook-test')

        # Assert repo exists in build location
        self.assertTrue(os.path.exists('bunny-hook-test'))

        # Remove new repo
        shutil.rmtree('bunny-hook-test')
