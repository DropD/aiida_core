#-*- coding: utf8 -*-
"""
click parameter types for Codes
"""
import click
from click_completion import startswith
from click_spinner import spinner as cli_spinner

from aiida.cmdline.cliparams.paramtypes.node import NodeParam
from aiida.cmdline.dbenv_decorator import aiida_dbenv


class CodeParam(NodeParam):
    """
    handle verification and tab-completion (relies on click-completion) for Code db entries
    """
    name = 'aiida code'

    @property
    @aiida_dbenv
    def node_type(self):
        from aiida.orm import Code
        return Code

    def get_possibilities(self, incomplete=''):
        """
        get all possible options for codes starting with incomplete

        :return: list of tuples with (name, help)
        """
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
    def convert(self, value, param, ctx):
        """
        check the given value corresponds to a code in the db, raise BadParam else

        gets the corresponding code object from the database for a pk or name
        and returns that
        """
        from aiida.orm import Code
        codes = [c[0] for c in self.get_possibilities()]
        if value not in codes:
            raise click.BadParameter('Must be a code in you database', param=param)

        try:
            # assume is pk
            value = int(value)
            if value < 1:
                raise click.BadParameter("PK values start from 1")
            code = Code.get(pk=value)
        except:
            # assume is label
            code = Code.get(label=value)

        if self.get_from_db:
            value = code
        elif self.pass_pk:
            value = code.pk
        else:
            value = code.uuid
        return value


class CodeNameParam(click.ParamType):
    """
    verify there is no @ sign in the name
    """
    name = 'code label'

    def convert(self, value, param, ctx):
        """
        check if valid code name
        """
        value = super(CodeNameParam, self).convert(value, param, ctx)
        if '@' in value:
            raise click.BadParameter("Code labels may not contain the '@' sign", param=param)
        return value


@aiida_dbenv
def get_code_data():
    """
    Retrieve the list of codes in the DB.
    Return a tuple with (pk, label, computername, owneremail).

    :param django_filter: a django query object (e.g. obtained
      with Q()) to filter the results on the AiidaOrmCode class.
    """
    from aiida.orm import Code as AiidaOrmCode
    from aiida.orm.querybuilder import QueryBuilder

    qb = QueryBuilder()
    qb.append(AiidaOrmCode, project=['id', 'label'])
    qb.append(type='computer', computer_of=AiidaOrmCode, project=['name'])
    qb.append(type='user', creator_of=AiidaOrmCode, project=['email'])

    return sorted(qb.all())