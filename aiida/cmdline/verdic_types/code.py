#-*- coding: utf8 -*-
"""
click parameter types for Codes
"""
import click
from click_completion import startswith
from click_spinner import spinner as cli_spinner

from aiida.cmdline.verdic_utils import aiida_dbenv


class CodeArgument(click.ParamType):
    """
    handle verification and tab-completion (relies on click-completion) for Code db entries
    """
    name = 'aiida code'

    def get_possibilities(self, incomplete=''):
        """
        get all possible options for codes starting with incomplete

        :return: list of tuples with (name, help)
        """
        from aiida.cmdline.verdic_utils import get_code_data
        names = [(c[1], c[2]) for c in get_code_data() if startswith(c[1], incomplete)]
        pks = [(str(c[0]), c[1]) for c in get_code_data() if startswith(str(c[0]), incomplete)]
        possibilities = names + pks
        return possibilities

    @aiida_dbenv
    def complete(self, ctx, incomplete):
        """
        load dbenv and run spinner while getting completions
        """
        with cli_spinner():
            suggestions = self.get_possibilities(incomplete=incomplete)
        return suggestions

    @aiida_dbenv
    def get_missing_message(self, param):
        with cli_spinner():
            code_item = '{:<12} {}'
            codes = [code_item.format(*p) for p in self.get_possibilities()]
        return 'Possible arguments are:\n\n' + '\n'.join(codes)

    @aiida_dbenv
    def unsafe_convert(self, value, param, ctx):
        """check the given value corresponds to a code in the db, raise BadParam else"""
        codes = [c[0] for c in self.get_possibilities()]
        if value not in codes:
            raise click.BadParameter('Must be a code in you database', param=param)
        return True, value

    def safe_convert(self, value, param, ctx):
        """check the given value corresponds to a code in the db, without raising"""
        result = False, value
        try:
            result = self.unsafe_convert(value, param, ctx)
        except click.BadParameter as e:
            click.echo(e.format_message())
            result = False, value
        return result
