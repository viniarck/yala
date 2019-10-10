"""Acceptance tests for yala executable."""
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from unittest import TestCase
from unittest.mock import patch

from yala.main import main


class TestAcceptance(TestCase):
    """Acceptance test."""

    @classmethod
    @patch('yala.main.sys.exit')
    @patch('yala.main.sys.stdout', new_callable=StringIO)
    @patch('yala.main.Pool')
    def setUpClass(cls, pool_mock, stdout_mock, exit_mock):
        """Get yala's output to be used in tests.

        As coverage outputs random results with --concurrency=multiprocessing,
        we use Python threads instead.
        """
        # Ignore params of patch decorators:
        # pylint: disable=arguments-differ
        cls._exit = exit_mock
        # Replace multiprocessing by Python threads
        pool_mock.return_value = ThreadPoolExecutor()
        with patch('yala.main.sys.argv', ['yala', 'tests_data/fake_code.py']):
            main()
        output = stdout_mock.getvalue()
        # Remove empty last line due to trailing '\n'
        cls._output = output.split('\n')[:-1]

    def _assert_results(self, lines, linter_name):
        """Assert all lines are in the output."""
        for line in lines:
            self._assert_result(line, linter_name)

    def _assert_result(self, line, linter_name):
        full_line = self._complete_output_line(line, linter_name)
        self.assertIn(full_line, self._output)

    def _assert_any_result(self, lines, linter_name):
        for line in lines:
            full_line = self._complete_output_line(line, linter_name)
            if full_line in self._output:
                return
        self.fail('None found: "{}"'.format('", "'.join(lines)))

    @staticmethod
    def _complete_output_line(line, linter_name):
        return 'tests_data/fake_code.py|{} [{}]'.format(line, linter_name)

    def test_exit_error(self):
        """Should exit with error if there's linter output."""
        arg = self._exit.call_args_list[0][0][0]
        self.assertTrue(arg, 'Exit argument should not be empty')

    def test_flake8(self):
        """Check pycodestyle output."""
        expected = (
            "1:1|F401 'os' imported but unused",
            "2:1|F401 'abc' imported but unused",
            "7:20|E211 whitespace before '('"
            )
        self._assert_results(expected, 'flake8')

    def test_isort(self):
        """Check isort output."""
        expected = 'None:None|Imports are incorrectly sorted.'
        self._assert_result(expected, 'isort')

    def test_mypy(self):
        """Check mypy output."""
        expected = "4:None|error: Need type comment for 'untyped_list' " + \
            '(hint: "untyped_list = ...  # type: List[<type>]")'
        expected_py37 = '4:None|error: Need type annotation for ' + \
            '\'untyped_list\' (hint: "untyped_list: List[<type>] = ...")'
        possible_results = expected, expected_py37
        self._assert_any_result(possible_results, 'mypy')

    def test_pycodestyle(self):
        """Check pycodestyle output."""
        expected = "7:20|E211 whitespace before '('"
        self._assert_result(expected, 'pycodestyle')

    def test_pydocstyle(self):
        """Check pydocstyle ouput."""
        expected = '1:None|D100: Missing docstring in public module'
        self._assert_result(expected, 'pydocstyle')

    def test_pyflakes(self):
        """Check Pyflakes output."""
        expected = (
            "1:None|'os' imported but unused",
            "2:None|'abc' imported but unused"
        )
        self._assert_results(expected, 'pyflakes')

    def test_pylint(self):
        """Check Pylint output."""
        expected = (
            '1:0|Missing module docstring (C0114, missing-module-docstring)',
            '1:0|Unused import os (W0611, unused-import)',
            '2:0|Unused import abc (W0611, unused-import)',
            '7:0|Too many branches (20/12) (R0912, too-many-branches)'
        )
        self._assert_results(expected, 'pylint')

    def test_rest_radon_cc(self):
        """Check radon cc ouput."""
        expected = '7:0|high_complexity - D'
        self._assert_result(expected, 'radon cc')
