#-*- coding: utf8 -*-
"""
Click parameter types for Codes
"""
import click
from click_completion import startswith
from click_spinner import spinner as cli_spinner

from aiida.cmdline.cliparams.paramtypes.node import NodeParam
from aiida.cmdline.dbenv_lazyloading import with_dbenv


class CodeParam(NodeParam):
    """
    Handle verification and tab-completion (relies on click-completion) for Code db entries
    """
    name = 'aiida code'

    @property
    @with_dbenv
    def node_type(self):
        from aiida.orm import Code
        return Code

    @staticmethod
    def get_possibilities(incomplete=''):
        """
        Get all possible options for codes starting with incomplete

        :return: list of tuples with (name, help)
        """
        names = [(c[1], c[2]) for c in get_code_data() if startswith(c[1], incomplete)]
        pks = [(str(c[0]), c[1]) for c in get_code_data() if startswith(str(c[0]), incomplete)]
        possibilities = names + pks
        return possibilities

    def complete(self, ctx=None, incomplete=''):
        """
        Load dbenv and run spinner while getting completions
        """
        with cli_spinner():
            suggestions = self.get_possibilities(incomplete=incomplete)
        return suggestions

    def get_missing_message(self, param):
        with cli_spinner():
            code_item = '{:<12} {}'
            codes = [code_item.format(*p) for p in self.get_possibilities()]
        return 'Possible arguments are:\n\n' + '\n'.join(codes)

    def convert(self, value, param, ctx):
        """
        Check the given value corresponds to a code in the db, raise BadParam else

        gets the corresponding code object from the database for a pk or name
        and returns that
        """
        codes = [c[0] for c in self.get_possibilities()]
        if value.split('@')[0] not in codes:
            raise click.BadParameter('Must be a code in you database', param=param)

        try:
            # assume is pk
            value = int(value)
            if value < 1:
                raise click.BadParameter("PK values start from 1")
            code = self.node_type.get(pk=value)
        except ValueError:
            # assume is label or name
            code = self.node_type.get_from_string(value)

        if self.get_from_db:
            value = code
        elif self.pass_pk:
            value = code.pk
        else:
            value = code.uuid
        return value


class CodeNameParam(click.ParamType):
    """
    Verify there is no @ sign in the name
    """
    name = 'code label'

    def convert(self, value, param, ctx):
        """
        Check if valid code name
        """
        value = super(CodeNameParam, self).convert(value, param, ctx)
        if '@' in value:
            raise click.BadParameter("Code labels may not contain the '@' sign", param=param)
        return value


@with_dbenv
def get_code_data():
    """
    Retrieve the list of codes in the DB.
    Return a tuple with (pk, label, computername, owneremail).

    :param django_filter: a django query object (e.g. obtained
      with Q()) to filter the results on the AiidaOrmCode class.
    """
    from aiida.orm import Code as AiidaOrmCode
    from aiida.orm.querybuilder import QueryBuilder

    query_builder = QueryBuilder()
    query_builder.append(AiidaOrmCode, project=['id', 'label'])
    query_builder.append(type='computer', computer_of=AiidaOrmCode, project=['name'])
    query_builder.append(type='user', creator_of=AiidaOrmCode, project=['email'])

    return sorted(query_builder.all())
