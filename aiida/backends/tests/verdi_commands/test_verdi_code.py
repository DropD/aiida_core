"""Test verdi code and subcommands"""
import re

import click
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.control.code import CodeBuilder
from aiida.common.exceptions import NotExistent


class VerdiCodeTest(AiidaTestCase):
    """Test the ``verdi code`` command group"""

    def setUp(self):
        super(VerdiCodeTest, self).setUp()
        from aiida.cmdline.commands.code import code
        self.code_grp = code
        self.runner = CliRunner()
        self.code_label = 'test_code'

    def tearDown(self):
        self.clean_db()
        self.insert_data()

    def _create_code(self):
        from aiida.orm import Computer
        builder = CodeBuilder(
            code_type=CodeBuilder.CodeType.ON_COMPUTER,
            remote_abs_path='/fantasy/path/to/executable',
            computer=Computer.get('localhost'),
            label=self.code_label,
            description='description',
            input_plugin='simpleplugins.templatereplacer',
            prepend_text='',
            append_text='')
        code = builder.new()
        code.store()
        return code

    def _invoke(self, *args):
        return self.runner.invoke(self.code_grp, args)

    def test_help(self):
        result = self._invoke('--help')
        self.assertFalse(result.exception)
        self.assertIn(member='Usage: ', container=result.output)

    def test_show(self):
        """Make sure ``code show`` can be called with a label or pk and returns some output containing label and desc"""
        code = self._create_code()

        # invoke with label as argument, ensure no exceptions and output reasonable
        result = self._invoke('show', self.code_label)
        self.assertFalse(
            bool(result.exception),
            msg='{}\noutput was:\n{}'.format(
                repr(result.exception), result.output))
        label_regex = r'.*Label:.*{}'.format(self.code_label)
        description_regex = r'.*Description:\s*{}'.format(code.description)
        self.assertTrue(
            re.match(label_regex, result.output, re.DOTALL),
            msg='{}\ndid not match output \n{}'.format(label_regex,
                                                       result.output))
        self.assertTrue(
            re.match(description_regex, result.output, re.DOTALL),
            msg='{}\ndid not match output \n{}'.format(description_regex,
                                                       result.output))

        # invoke with pk as argument, ensure same output
        result_pk = self._invoke('show', str(code.pk))
        self.assertEqual(result.output, result_pk.output)

    def test_delete_label(self):
        """Make sure ``code delete`` can be called with pk and works"""
        from aiida.orm import Code
        self._create_code()

        # invoke with label as argument, make sure it works
        result = self._invoke('delete', self.code_label)
        self.assertFalse(
            bool(result.exception),
            msg='{}\noutput was:\n{}'.format(
                repr(result.exception), result.output))
        with self.assertRaises(NotExistent):
            Code.get(label=self.code_label)

    def test_delete_pk(self):
        """Make sure ``code delete`` can be called with label and works"""
        from aiida.orm import Code
        code = self._create_code()

        # invoke with pk as argument, make sure it deletes the code
        result_pk = self._invoke('delete', str(code.pk))
        self.assertFalse(
            bool(result_pk.exception),
            msg='{}\noutput was:\n{}'.format(
                repr(result_pk.exception), result_pk.output))
        with self.assertRaises(NotExistent):
            Code.get(label=self.code_label)

    def test_no_delete_with_children(self):
        """Test that ``code delete`` does not delete codes with children"""
        from aiida.orm import CalculationFactory
        from aiida.orm import Code
        code = self._create_code()
        calc = CalculationFactory('simpleplugins.templatereplacer')()
        calc.use_code(code)
        calc.set_computer(code.get_computer())
        calc.set_resources({'num_machines': '1', 'tot_num_mpiprocs': '1'})
        calc.store()
        result = self._invoke('delete', self.code_label)
        self.assertIsInstance(result.exception, SystemExit)
        Code.get(label=self.code_label)

    def test_update_options(self):
        """Test updating a code successfully"""
        from aiida.orm import Code
        code = self._create_code()

        new_label = 'new_label'
        self.assertNotEqual(new_label, code.label)
        new_input_plugin = 'aseplugins.ase'
        self.assertNotEqual(new_input_plugin, code.get_input_plugin_name())
        new_desc = 'new description'
        self.assertNotEqual(new_desc, code.description)
        new_prepend = 'new prepend'
        self.assertNotEqual(new_prepend, code.get_prepend_text())
        new_append = 'new_append'
        self.assertNotEqual(new_append, code.get_append_text())
        new_location = '/path/to/another/fantasy/executable'
        self.assertNotEqual(new_location, code.get_remote_exec_path())

        result = self._invoke(
            'update', '--label', new_label,
            '--description', new_desc,
            '--input-plugin', new_input_plugin,
            '--prepend-text', new_prepend,
            '--append-text', new_append,
            '--remote-abs-path', new_location)  # yapf: disable
        self.assertFalse(bool(result.exception))
        code = Code.get(label=new_label)
        self.assertEquals(code.description, new_desc)
        self.assertEquals(code.get_input_plugin_name(), new_input_plugin)
        self.assertEquals(code.get_prepend_text(), new_prepend)
        self.assertEquals(code.get_append_text(), new_append)
        self.assertEquals(code.get_remote_exec_path(), new_location)
