"""Test verdi code and subcommands"""
import re

from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.control.code import CodeBuilder


class VerdiCodeTest(AiidaTestCase):
    """Test the ``verdi code`` command group"""

    def setUp(self):
        super(VerdiCodeTest, self).setUp()
        from aiida.cmdline.commands.code import code
        self.code_grp = code
        self.runner = CliRunner()

    def _create_code(self):
        from aiida.orm import Computer
        builder = CodeBuilder(
            code_type=CodeBuilder.CodeType.ON_COMPUTER,
            remote_abs_path='/fantasy/path/to/executable',
            computer=Computer.get('localhost'),
            label='test_code',
            description='description',
            input_plugin='simpleplugins.templatereplacer',
            prepend_text='',
            append_text=''
        )
        return builder.new()

    def _invoke(self, *args):
        return self.runner.invoke(self.code_grp, args)

    def test_help(self):
        result = self._invoke('--help')
        self.assertFalse(result.exception)
        self.assertIn(member='Usage: ', container=result.output)

    def test_show(self):
        code = self._create_code()
        code.store()
        result = self._invoke(['show', code.label])
        self.assertFalse(result.exception)
        self.assertTrue(re.match(r'Label:\s*{}'.format(code.label), result.output))
        self.assertTrue(re.match(r'Description:\s*{}'.format(code.description), result.description))
