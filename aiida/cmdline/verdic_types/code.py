#-*- coding: utf8 -*-
"""
click parameter types for Codes
"""
import click
from click_completion import startswith
from click_spinner import spinner as cli_spinner

from aiida.cmdline.verdic_utils import aiida_dbenv


class CodeArgument(click.ParamType):
    '''
    handle tab-completion (relies on click-completion) for Code db entries
    '''
    def get_possibilities(self, incomplete=''):
        from aiida.cmdline.verdic_utils import get_code_data
        names = [(c[1], c[2]) for c in get_code_data() if startswith(c[1], incomplete)]
        pks = [(str(c[0]), c[1]) for c in get_code_data() if startswith(str(c[0]), incomplete)]
        possibilities = names + pks
        return possibilities

    @aiida_dbenv
    def complete(self, ctx, incomplete):
        with cli_spinner():
            suggestions = self.get_possibilities(incomplete=incomplete)
        return suggestions

    @aiida_dbenv
    def get_missing_message(self, param):
        with cli_spinner():
            code_item = '{:<12} {}'
            codes = [code_item.format(*p) for p in self.get_possibilities()]
        return 'Possible arguments are:\n\n' + '\n'.join(codes)

