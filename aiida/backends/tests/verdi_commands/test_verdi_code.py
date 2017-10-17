"""Test verdi code and subcommands"""
import re
from os.path import dirname, abspath, basename

from click.testing import CliRunner
from mock import mock

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.cliparams.templates import env
from aiida.common.exceptions import NotExistent
from aiida.control.code import CodeBuilder
from aiida.orm import Code, Computer


class VerdiCodeTest(AiidaTestCase):
    """Test the ``verdi code`` command group"""

    def setUp(self):
        super(VerdiCodeTest, self).setUp()
        from aiida.cmdline.commands.code import code
        self.code_grp = code
        self.runner = CliRunner()
        self.code_label = 'test_code'
        self.code_data = {
            'code_type': CodeBuilder.CodeType.ON_COMPUTER,
            'remote_abs_path': '/fantasy/path/to/executable',
            'computer': Computer.get('localhost'),
            'label': self.code_label,
            'description': 'description',
            'input_plugin': 'simpleplugins.templatereplacer',
            'prepend_text': '',
            'append_text': ''
        }

    def tearDown(self):
        self.clean_db()
        self.insert_data()

    def _create_code(self):
        """Create a test code"""
        builder = CodeBuilder(**self.code_data)
        code = builder.new()
        code.store()
        return code

    def _invoke(self, *args, **kwargs):
        return self.runner.invoke(self.code_grp, args, **kwargs)

    def test_help(self):
        result = self._invoke('--help')
        self.assert_noexcept(result)
        self.assertIn(member='Usage: ', container=result.output)

    def test_show(self):
        """Make sure ``code show`` can be called with a label or pk and returns some output containing label and desc"""
        code = self._create_code()

        # invoke with label as argument, ensure no exceptions and output reasonable
        result = self._invoke('show', self.code_label)
        self.assert_noexcept(result)
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
        self._create_code()

        # invoke with label as argument, make sure it works
        result = self._invoke('delete', self.code_label)
        self.assert_noexcept(result)
        with self.assertRaises(NotExistent):
            Code.get(label=self.code_label)

    def updated_values(self, code):
        """New values to test updating"""

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

        return {
            'label': new_label,
            'input-plugin': new_input_plugin,
            'description': new_desc,
            'prepend-text': new_prepend,
            'append-text': new_append,
            'remote-abs-path': new_location
        }

    def assert_code(self, data, result):
        """Compare code attributes agains a dictionary of values"""
        code = Code.get(label=data['label'])
        self.assertEquals(
            code.description, data['description'], msg=result.output)

        input_plugin = data.get('input-plugin', data.get('input_plugin'))
        if input_plugin:
            self.assertEquals(
                code.get_input_plugin_name(), input_plugin, msg=result.output)

        prepend_text = data.get('prepend-text', data.get('prepend_text'))
        if prepend_text:
            self.assertEquals(
                code.get_prepend_text(), prepend_text, msg=result.output)

        append_text = data.get('append-text', data.get('append_text'))
        if append_text:
            self.assertEquals(
                code.get_append_text(), append_text, msg=result.output)

        remote_abs_path = data.get('remote-abs-path',
                                   data.get('remote_abs_path'))
        if remote_abs_path:
            self.assertEqual(
                code.get_remote_exec_path(), remote_abs_path, msg=result.output)

        code_folder = data.get('code-rel-path', data.get('code_rel_path'))
        if code_folder:
            self.assertEqual(
                code.get_local_executable(), code_folder, msg=result.output)

    def assert_noexcept(self, result):
        self.assertFalse(
            bool(result.exception),
            msg='{}\noutput was:\n{}'.format(
                repr(result.exception), result.output))

    def test_delete_pk(self):
        """Make sure ``code delete`` can be called with label and works"""
        code = self._create_code()

        # invoke with pk as argument, make sure it deletes the code
        result_pk = self._invoke('delete', str(code.pk))
        self.assert_noexcept(result_pk)
        with self.assertRaises(NotExistent):
            Code.get(label=self.code_label)

    def test_no_delete_with_children(self):
        """Test that ``code delete`` does not delete codes with children"""
        from aiida.orm import CalculationFactory
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
        """Test updating a code noninteractively successfully"""
        code = self._create_code()
        new_data = self.updated_values(code)

        result = self._invoke(
            'update', self.code_label, '--non-interactive',
            '--label', new_data['label'],
            '--description', new_data['description'],
            '--input-plugin', new_data['input-plugin'],
            '--prepend-text', new_data['prepend-text'],
            '--append-text', new_data['append-text'],
            '--remote-abs-path', new_data['remote-abs-path'])  # yapf: disable
        self.assert_noexcept(result)
        self.assert_code(new_data, result)

    def test_update_prompt(self):
        """Test updating a code interactively"""
        code = self._create_code()
        new_data = self.updated_values(code)

        prepost = env.get_template('prepost.bash.tpl').render(
            default_pre=new_data['prepend-text'],
            default_post=new_data['append-text'],
            summary={})
        with mock.patch('click.edit', return_value=prepost):
            result = self._invoke(
                'update',
                self.code_label,
                input=
                '{label}\n{description}\n{input-plugin}\n{remote-abs-path}\ny\n'.
                format(**new_data))
        self.assert_noexcept(result)
        self.assert_code(new_data, result)

    def test_update_prompt_noconfirm(self):
        """Test updating a code interactively"""
        code = self._create_code()
        old_remote_abs_path = code.get_remote_exec_path()
        new_data = self.updated_values(code)

        prepost = env.get_template('prepost.bash.tpl').render(
            default_pre=new_data['prepend-text'],
            default_post=new_data['append-text'],
            summary={})
        with mock.patch('click.edit', return_value=prepost):
            result = self._invoke(
                'update',
                self.code_label,
                input=
                '{label}\n{description}\n{input-plugin}\n{remote-abs-path}\nn\n'.
                format(**new_data))
        self.assert_noexcept(result)
        new_data['remote-abs-path'] = old_remote_abs_path
        self.assert_code(new_data, result)

    def test_update_prompt_defaults(self):
        """Test updating without actually changing anything"""
        code = self._create_code()

        prepost = env.get_template('prepost.bash.tpl').render(
            default_pre=code.get_prepend_text(),
            default_post=code.get_append_text(),
            summary={})
        with mock.patch('click.edit', return_value=prepost):
            result = self._invoke('update', self.code_label, input='\n\n\n\n')
        self.assert_noexcept(result)

    def test_rename(self):
        """Test renaming a code"""
        self._create_code()
        result = self._invoke('rename', self.code_label, 'test_rename')
        self.assert_noexcept(result)
        self.assertTrue(Code.get(label='test_rename'))

    def test_rename_invalid_arg(self):
        """Test renaming a code"""
        self._create_code()
        result = self._invoke('rename', self.code_label,
                              'test_rename@problematic')
        self.assertIsNotNone(result.exception)
        with self.assertRaises(NotExistent):
            Code.get(label='test_rename@problematic')

        result = self._invoke('rename', self.code_label + '@localhost',
                              'test_rename')
        self.assert_noexcept(result)
        self.assertTrue(Code.get(label='test_rename'))

    def test_setup_prompt_remote(self):
        """Test setting up a code"""
        prepost = env.get_template('prepost.bash.tpl').render(
            default_pre=self.code_data['prepend_text'],
            default_post=self.code_data['append_text'],
            summary={})
        data = {
            'label': self.code_data['label'],
            'description': self.code_data['description'],
            'input_plugin': self.code_data['input_plugin'],
            'computer': self.code_data['computer'].name,
            'remote_abs_path': self.code_data['remote_abs_path']
        }
        prompt_input = '{label}\n{description}\nTrue\n{input_plugin}\n{computer}\n{remote_abs_path}\n'.format(
            **data)
        with mock.patch('click.edit', return_value=prepost):
            result = self._invoke(
                'setup', input=prompt_input, catch_exceptions=False)

        self.assert_noexcept(result)
        self.assert_code(data, result)

    def test_setup_prompt_local(self):
        """Test setting up a local code"""
        prepost = env.get_template('prepost.bash.tpl').render(
            default_pre=self.code_data['prepend_text'],
            default_post=self.code_data['append_text'],
            summary={})
        data = {
            'label': self.code_data['label'],
            'description': self.code_data['description'],
            'input_plugin': self.code_data['input_plugin'],
            'code_folder': abspath(dirname(__file__)),
            'code_rel_path': basename(__file__)
        }
        prompt_input = '{label}\n{description}\nFalse\n{input_plugin}\n{code_folder}\n{code_rel_path}\n'.format(
            **data)
        with mock.patch('click.edit', return_value=prepost):
            result = self._invoke(
                'setup', input=prompt_input, catch_exceptions=False)

        self.assert_noexcept(result)
        self.assert_code(data, result)

    def test_setup_options_remote(self):
        """Test setting up a code non-interactively"""
        result = self._invoke(
            'setup', '--non-interactive', '--on-computer',
            '--label={}'.format(self.code_data['label']),
            '--description={}'.format(self.code_data['description']),
            '--input-plugin={}'.format(self.code_data['input_plugin']),
            '--computer={}'.format(self.code_data['computer'].name),
            '--remote-abs-path={}'.format(self.code_data['remote_abs_path']))
        self.assert_noexcept(result)
        self.assert_code(self.code_data, result)
