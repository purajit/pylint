# Copyright (c) 2006-2011, 2013-2014 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2015-2016 Claudiu Popa <pcmanticore@gmail.com>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

"""non regression tests for pylint, which requires a too specific configuration
to be incorporated in the automatic functional test framework
"""

import sys
import os
from os.path import abspath, dirname, join

import pytest

import astroid
import pylint.testutils as testutils
from pylint import checkers
from pylint import epylint
from pylint import lint

test_reporter = testutils.TestReporter()
linter = lint.PyLinter()
linter.set_reporter(test_reporter)
linter.disable('I')
linter.config.persistent = 0
checkers.initialize(linter)

REGR_DATA = join(dirname(abspath(__file__)), 'regrtest_data')
sys.path.insert(1, REGR_DATA)

try:
    PYPY_VERSION_INFO = sys.pypy_version_info
except AttributeError:
    PYPY_VERSION_INFO = None

class TestNonRegr(object):
    def setup_method(self):
        """call reporter.finalize() to cleanup
        pending messages if a test finished badly
        """
        linter.reporter.finalize()

    def test_package___path___manipulation(self):
        linter.check('package.__init__')
        got = linter.reporter.finalize().strip()
        assert got == ''

    def test_package___init___precedence(self):
        linter.check('precedence_test')
        got = linter.reporter.finalize().strip()
        assert got == ''

    def test_check_package___init__(self):
        filename = 'package.__init__'
        linter.check(filename)
        checked = list(linter.stats['by_module'].keys())
        assert checked == ['package.__init__'], '%s: %s' % (filename, checked)

        cwd = os.getcwd()
        os.chdir(join(REGR_DATA, 'package'))
        sys.path.insert(0, '')
        try:
            linter.check('__init__')
            checked = list(linter.stats['by_module'].keys())
            assert checked == ['__init__'], checked
        finally:
            sys.path.pop(0)
            os.chdir(cwd)

    def test_class__doc__usage(self):
        linter.check(join(REGR_DATA, 'classdoc_usage.py'))
        got = linter.reporter.finalize().strip()
        assert got == ''

    def test_package_import_relative_subpackage_no_attribute_error(self):
        linter.check('import_package_subpackage_module')
        got = linter.reporter.finalize().strip()
        assert got == ''

    def test_import_assign_crash(self):
        linter.check(join(REGR_DATA, 'import_assign.py'))

    def test_special_attr_scope_lookup_crash(self):
        linter.check(join(REGR_DATA, 'special_attr_scope_lookup_crash.py'))

    def test_module_global_crash(self):
        linter.check(join(REGR_DATA, 'module_global.py'))
        got = linter.reporter.finalize().strip()
        assert got == ''

    def test_decimal_inference(self):
        linter.check(join(REGR_DATA, 'decimal_inference.py'))
        got = linter.reporter.finalize().strip()
        assert got == ""

    def test_descriptor_crash(self):
        for fname in os.listdir(REGR_DATA):
            if fname.endswith('_crash.py'):
                linter.check(join(REGR_DATA, fname))
                linter.reporter.finalize().strip()

    def test_try_finally_disable_msg_crash(self):
        linter.check(join(REGR_DATA, 'try_finally_disable_msg_crash'))

    def test___path__(self):
        linter.check('pylint.checkers.__init__')
        messages = linter.reporter.finalize().strip()
        assert not ('__path__' in messages), messages

    def test_absolute_import(self):
        linter.check(join(REGR_DATA, 'absimp', 'string.py'))
        got = linter.reporter.finalize().strip()
        assert got == ""

    def test_no_context_file(self):
        expected = "Unused import missing"
        linter.check(join(REGR_DATA, 'bad_package'))
        got = linter.reporter.finalize().strip()
        assert expected in got

    @pytest.mark.skipif(PYPY_VERSION_INFO and PYPY_VERSION_INFO < (4, 0),
                        reason="On older PyPy versions, sys.executable was set to a value "
                        "that is not supported by the implementation of this function. "
                        "( https://bitbucket.org/pypy/pypy/commits/19e305e27e67 )")
    def test_epylint_does_not_block_on_huge_files(self):
        path = join(REGR_DATA, 'huge.py')
        out, err = epylint.py_run(path, return_std=True)
        assert hasattr(out, 'read')
        assert hasattr(err, 'read')
        output = out.read(10)
        assert isinstance(output, str)

    def test_pylint_config_attr(self):
        mod = astroid.MANAGER.ast_from_module_name('pylint.lint')
        pylinter = mod['PyLinter']
        expect = ['OptionsManagerMixIn', 'object', 'MessagesHandlerMixIn',
                  'ReportsHandlerMixIn', 'BaseTokenChecker', 'BaseChecker',
                  'OptionsProviderMixIn']
        assert [c.name for c in pylinter.ancestors()] == expect
        assert list(astroid.Instance(pylinter).getattr('config'))
        inferred = list(astroid.Instance(pylinter).igetattr('config'))
        assert len(inferred) == 1
        assert inferred[0].root().name == 'optparse'
        assert inferred[0].name == 'Values'
