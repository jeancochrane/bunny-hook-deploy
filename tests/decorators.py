from unittest.mock import create_autospec
from subprocess import CompletedProcess


def mock_commands(func):
    '''
    Decorator for mocking Worker.run_command.
    '''
    def new_test(self, *args, **kwargs):
        return_value = CompletedProcess([], returncode=0)

        self.worker.run_command = create_autospec(self.worker.run_command,
                                                return_value=return_value)
        func(self, *args, **kwargs)

    return new_test

def mock_scripts(func):
    '''
    Decorator for mocking Worker.run_script.
    '''
    def new_test(self, *args, **kwargs):
        return_value = CompletedProcess([], returncode=0)

        self.worker.run_script = create_autospec(self.worker.run_script,
                                                return_value=return_value)
        func(self, *args, **kwargs)

    return new_test

def mock_subprocess(func):
    '''
    Decorator for mocking all subprocess calls in Worker.
    '''
    return mock_scripts(mock_commands(func))
