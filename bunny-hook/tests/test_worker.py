import os
from unittest import TestCase, main
import logging

import env
from api.worker import Worker
from api.exceptions import WorkerException
from decorators import mock_subprocess


class TestWorker(TestCase):

    def setUp(self):
        payload = {
            'ref': 'refs/head/master',
            'repository': {
                'name': 'bunny-hook'
            },
            'clone_url': 'https://github.com/jeancochrane/bunny-hook.git'
        }

        self.worker = Worker(payload)

        # Suppress stdout logging
        logging.disable(logging.INFO)

    def path_to(self, relpath):
        '''
        Get the absolute path of a file relative to the tests directory. This method
        helps ensure that we can run tests from multiple locations (either
        the root directory, or the tests directory).
        '''
        inpath = relpath.split('/')
        cwd = os.path.split(os.getcwd())[-1]

        if cwd == 'bunny-hook':
            return os.path.join(os.getcwd(), 'tests', *inpath)

        elif cwd == 'tests':
            return os.path.join(os.getcwd(), *inpath)

        else:
            msg = ('Running tests from the directory {dr} is not supported.'.format(dr=os.getcwd()) +
                   ' Run tests from `bunny-hook` or `tests` instead.')
            raise Exception(msg)

    def test_run_command_succeeds(self):
        cmd = self.worker.run_command(['echo'])
        self.assertEqual(cmd.returncode, 0)

    def test_run_command_errors(self):
        with self.assertRaises(WorkerException) as e:
            self.worker.run_command(['bash', 'exit', '1'])

    def test_run_script(self):
        script = self.path_to('scripts/pass.sh')
        cmd = self.worker.run_script(script)
        self.assertEqual(cmd.returncode, 0)

    def test_run_script_errors(self):
        script = self.path_to('scripts/fail.sh')
        with self.assertRaises(WorkerException) as e:
            self.worker.run_script(script)

    @mock_subprocess
    def test_deploy_without_commands(self):
        '''
        Mock out all subprocess calls and test that the rest of the `deploy`
        command runs.
        '''
        good_config = self.path_to('configs/good-configs')
        deployed = self.worker.deploy(tmp_path=good_config)
        self.assertTrue(deployed)

    @mock_subprocess
    def test_empty_config_file(self):
        '''
        Test an error is raised when the config file is found, but empty.
        '''
        empty_config = self.path_to('configs/empty-config')
        with self.assertRaises(WorkerException) as e:
            self.worker.deploy(tmp_path=empty_config)

        expected_msg = 'deploy.yml appears to be empty'
        self.assertIn(expected_msg, str(e.exception))

    @mock_subprocess
    def test_no_config_file(self):
        '''
        Test an error is raised when no config file is found.
        '''
        no_config = self.path_to('.')
        with self.assertRaises(WorkerException) as e:
            self.worker.deploy(tmp_path=no_config)

        expected_msg = 'Could not locate a `deploy.yml` file in your repo'
        self.assertIn(expected_msg, str(e.exception))

    @mock_subprocess
    def test_two_config_files(self):
        '''
        Test an error is raised when two config files are found.
        '''
        two_configs = self.path_to('configs/two-configs')
        with self.assertRaises(WorkerException) as e:
            self.worker.deploy(tmp_path=two_configs)

        expected_msg = 'Found two config files in this repo! Delete one and try again'
        self.assertIn(expected_msg, str(e.exception))

    @mock_subprocess
    def test_no_clone_directive_in_config_file(self):
        '''
        Test that an error is raised when no clone directive is found in the
        config file.
        '''
        no_clone_config = self.path_to('configs/no-clone')
        with self.assertRaises(WorkerException) as e:
            self.worker.deploy(tmp_path=no_clone_config)

        expected_msg = 'is missing `home` directive'
        self.assertIn(expected_msg, str(e.exception))
