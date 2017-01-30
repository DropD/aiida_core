import sys
import click
from click_completion import startswith
from click_spinner import spinner as cli_spinner

from aiida.cmdline import verdic_options

def load_dbenv_if_not_loaded():
    with cli_spinner():
        from aiida.backends.utils import load_dbenv, is_dbenv_loaded
        if not is_dbenv_loaded():
            load_dbenv()

def aiida_dbenv(function):
    def decorated_function(*args, **kwargs):
        load_dbenv_if_not_loaded()
        return function(*args, **kwargs)
    return decorated_function

@click.group()
def code():
    """
    manage codes in your AiiDA database.
    """

def print_list_res(qb_query, show_owner):
    if qb_query.count > 0:
        for tuple_ in qb_query.all():
            if len(tuple_) == 3:
                (pk, label, useremail) = tuple_
                computername = None
            elif len(tuple_) == 4:
                (pk, label, useremail, computername) = tuple_
            else:
                print "Wrong tuple size"
                return

            if show_owner:
                owner_string = " ({})".format(useremail)
            else:
                owner_string = ""
            if computername is None:
                computernamestring = ""
            else:
                computernamestring = "@{}".format(computername)
            print "* pk {} - {}{}{}".format(
                pk, label, computernamestring, owner_string)
    else:
        print "# No codes found matching the specified criteria."

@code.command('list')
@click.option('-c', '--computer', help='filter codes for a computer')
@click.option('-p', '--plugin', help='filter codes for a plugin')
@click.option('-A', '--all-users', help='show codes of all users')
@click.option('-o', '--show-owner', is_flag=True, help='show owner information')
@click.option('-a', '--all-codes', is_flag=True, help='show hidden codes')
def _list(computer, plugin, all_users, show_owner, all_codes):
    """
    List available codes
    """
    load_dbenv_if_not_loaded()

    computer_filter = computer
    plugin_filter = plugin
    reveal_filter = all_codes

    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.code import Code
    from aiida.orm.computer import Computer
    from aiida.orm.user import User
    from aiida.backends.utils import get_automatic_user

    qb_user_filters = dict()
    if not all_users:
        user = User(dbuser=get_automatic_user())
        qb_user_filters['email'] = user.email

    qb_computer_filters = dict()
    if computer_filter is not None:
        qb_computer_filters['name'] = computer_filter

    qb_code_filters = dict()
    if plugin_filter is not None:
        qb_code_filters['attributes.input_plugin'] = plugin_filter

    if not reveal_filter:
        qb_code_filters['attributes.hidden'] = {"~==": True}

    print "# List of configured codes:"
    print "# (use 'verdi code show CODEID | CODENAME' to see the details)"
    if computer_filter is not None:
        qb = QueryBuilder()
        qb.append(Code, tag="code",
                    filters=qb_code_filters,
                    project=["id", "label"])
        # We have a user assigned to the code so we can ask for the
        # presence of a user even if there is no user filter
        qb.append(User, creator_of="code",
                    project=["email"],
                    filters=qb_user_filters)
        # We also add the filter on computer. This will automatically
        # return codes that have a computer (and of course satisfy the
        # other filters). The codes that have a computer attached are the
        # remote codes.
        qb.append(Computer, computer_of="code",
                    project=["name"],
                    filters=qb_computer_filters)
        print_list_res(qb, show_owner)

    # If there is no filter on computers
    else:
        # Print all codes that have a computer assigned to them
        # (these are the remote codes)
        qb = QueryBuilder()
        qb.append(Code, tag="code",
                    filters=qb_code_filters,
                    project=["id", "label"])
        # We have a user assigned to the code so we can ask for the
        # presence of a user even if there is no user filter
        qb.append(User, creator_of="code",
                    project=["email"],
                    filters=qb_user_filters)
        qb.append(Computer, computer_of="code",
                    project=["name"])
        print_list_res(qb, show_owner)

        # Now print all the local codes. To get the local codes we ask
        # the dbcomputer_id variable to be None.
        qb = QueryBuilder()
        comp_non_existence = {"dbcomputer_id": {"==": None}}
        if not qb_code_filters:
            qb_code_filters = comp_non_existence
        else:
            new_qb_code_filters = {"and": [qb_code_filters,
                                    comp_non_existence]}
            qb_code_filters = new_qb_code_filters
        qb.append(Code, tag="code",
                    filters=qb_code_filters,
                    project=["id", "label"])
        # We have a user assigned to the code so we can ask for the
        # presence of a user even if there is no user filter
        qb.append(User, creator_of="code",
                    project=["email"],
                    filters=qb_user_filters)
        print_list_res(qb, show_owner)

def get_code(code_id):
    """
    Get a Computer object with given identifier, that can either be
    the numeric ID (pk), or the label (if unique).

    .. note:: If an string that can be converted to an integer is given,
        the numeric ID is verified first (therefore, is a code A with a
        label equal to the ID of another code B is present, code A cannot
        be referenced by label).
    """
    from aiida.common.exceptions import NotExistent, MultipleObjectsError

    from aiida.orm import Code as AiidaOrmCode

    try:
        return AiidaOrmCode.get_from_string(code_id)
    except (NotExistent, MultipleObjectsError) as e:
        print >> sys.stderr, e.message
        sys.exit(1)

@aiida_dbenv
def get_code_data(django_filter=None):
    """
    Retrieve the list of codes in the DB.
    Return a tuple with (pk, label, computername, owneremail).

    :param django_filter: a django query object (e.g. obtained
        with Q()) to filter the results on the AiidaOrmCode class.
    """
    from aiida.orm import Code as AiidaOrmCode
    from aiida.orm.querybuilder import QueryBuilder

    qb = QueryBuilder()
    qb.append(AiidaOrmCode, project=['id', 'label', 'description'])
    qb.append(type='computer', computer_of=AiidaOrmCode, project=['name'])
    qb.append(type='user', creator_of=AiidaOrmCode, project=['email'])

    return sorted(qb.all())


def complete_code_names():
    code_names = [c[1] for c in get_code_data()]
    return "\n".join(code_names)

def complete_code_pks():
    code_pks = [str(c[0]) for c in get_code_data()]
    return "\n".join(code_pks)

def complete_code_names_and_pks():
    return "\n".join([complete_code_names(),
                        complete_code_pks()])


class CodeArgument(click.ParamType):
    def get_possibilities(self, incomplete=''):
        names = [(c[1], c[2]) for c in get_code_data() if startswith(c[1], incomplete)]
        pks = [(str(c[0]), c[1]) for c in get_code_data() if startswith(str(c[0]), incomplete)]
        possibilities = names + pks
        return possibilities

    @aiida_dbenv
    def complete(self, ctx, incomplete):
        return self.get_possibilities(incomplete=incomplete)

    @aiida_dbenv
    def get_missing_message(self, param):
        code_item = '{:<12} {}'
        codes = [code_item.format(*p) for p in self.get_possibilities()]
        return 'Possible arguments are:\n\n' + '\n'.join(codes)

@code.command()
@click.argument('code', metavar='CODE', type=CodeArgument())
def show(code):
    """
    Show information on a given code
    """
    load_dbenv_if_not_loaded()

    code = get_code(code)
    print code.full_text_info

def prompt_help_loop(prompt=None, suggestions=None):
    def decorator(validator_func):
        def decorated_validator(ctx, param, value):
            prevalue = validator_func(ctx, param, value)
            if isinstance(ctx.obj, dict):
                if ctx.obj.get('nocheck'):
                    return prevalue or 'UNUSED'
            help = param.help or 'invalid input'
            if suggestions:
                help += '\none of:\n\t' + '\n\t'.join(suggestions())
            if not ctx.params.get('non_interactive'):
                if isinstance(ctx.obj, dict):
                    multiline = ctx.obj.get('multiline', [])
                    print ctx.obj
                    while param in multiline:
                        value = decorated_validator( ctx, param, click.prompt(prompt or param.prompt))
                    value = ctx.obj.get('multiline_val_'+param.opts[0])
                while validator_func(ctx, param, value) is None or value == '?':
                    click.echo(help)
                    value = decorated_validator(ctx, param, click.prompt(prompt or param.prompt, default=param.default))
            value = validator_func(ctx, param, value)
            if ctx.params.get('non_interactive') and not value:
                raise click.MissingParameter(ctx=ctx, param=param, param_hint='{} {}'.format(param.opts, help))
            return value
        return decorated_validator
    return decorator

@prompt_help_loop(prompt='Label')
def validate_label(ctx, param, value):
    return value or None

@prompt_help_loop(prompt='Description')
def validate_description(ctx, param, value):
    return value or None

@prompt_help_loop(prompt='Local')
def validate_local(ctx, param, value):
    if value in [True, 'True', 'true', 'T']:
        return True
    elif value in [False, 'False', 'false', 'F']:
        return False
    else:
        return None

@aiida_dbenv
def input_plugin_list():
    from aiida.common.pluginloader import existing_plugins
    from aiida.orm.calculation.job import JobCalculation
    return [p.rsplit('.', 1)[0] for p in existing_plugins(JobCalculation, 'aiida.orm.calculation.job')]

@prompt_help_loop(prompt='Default input plugin', suggestions=input_plugin_list)
def validate_input_plugin(ctx, param, value):
    pluginlist = input_plugin_list()
    if value in pluginlist:
        return value
    else:
        return None

def validate_path(prefix_opt=None, is_abs=False, **kwargs):
    def decorator(validator_func):
        def decorated_validator(ctx, param, value):
            from os import path
            from os.path import expanduser, isabs
            path_t = click.Path(**kwargs)
            value = validator_func(ctx, param, value)
            if isinstance(ctx.obj, dict):
                if ctx.obj.get('nocheck'):
                    return value or 'UNUSED'
            if value:
                try:
                    value = expanduser(value)
                    if prefix_opt:
                        value = path.join(ctx.params.get(prefix_opt), value)
                    if is_abs and not isabs(value):
                        return None
                    value = path_t.convert(value, param, ctx)
                except click.BadParameter as e:
                    if ctx.params.get('non_interactive'):
                        raise e
                    click.echo(e.format_message(), err=True)
                    value = None
            return validator_func(ctx, param, value)
        return decorated_validator
    return decorator

def required_if_opt(opt=None, opt_value=None):
    """
    only verify parameter if opt is given in the context.

    In most cases opt should have is_eager set to True.
    """
    def decorator(validator_func):
        def decorated_validator(ctx, param, value):
            ctx.obj = {}
            if opt_value is not None:
                if isinstance(opt_value, (list, tuple)):
                    check = ctx.params.get(opt) in opt_value
                elif isinstance(opt_value, bool):
                    check = bool(ctx.params.get(opt)) is opt_value
                else:
                    check = ctx.params.get(opt) == opt_value
            else:
                check = bool(ctx.params.get(opt))
            if check:
                ctx.obj['nocheck'] = False
            else:
                ctx.obj['nocheck'] = True
            value = validator_func(ctx, param, value)
            if check and not value:
                return None
            else:
                return value
        return decorated_validator
    return decorator

@prompt_help_loop(prompt='Folder containing the code')
@validate_path(exists=True, file_okay=False, readable=True, resolve_path=True)
@required_if_opt(opt='is_local')
def validate_code_folder(ctx, param, value):
    return value

@prompt_help_loop(prompt='Relative path of the executable')
@validate_path(prefix_opt='code_folder', exists=True, dir_okay=False)
@required_if_opt(opt='is_local')
def validate_code_rel_path(ctx, param, value):
    return value

@prompt_help_loop(prompt='Remote computer name')
@required_if_opt(opt='is_local', opt_value=False)
def validate_computer(ctx, param, value):
    return value

@prompt_help_loop(prompt='Remote absolute path')
@validate_path(is_abs=True, dir_okay=False)
@required_if_opt(opt='is_local', opt_value=False)
def validate_code_remote_path(ctx, param, value):
    return value

@prompt_help_loop(prompt='# This is a multiline input, press CTRL+D on an\n# empty line to accept')
def validate_prepend_text(ctx, param, value):
    ctx.obj = ctx.obj or {}
    ctx.obj['multiline'] = ctx.obj.get('multiline') or []
    ctx.obj['multiline'].append(param)
    valkey = 'multiline_val_'+param.opts[0]
    ctx.obj[valkey] = ctx.obj.get(valkey) or []
    ctx.obj[valkey].append(value)
    print ctx.obj
    return None

@code.command()
@click.option('--label', is_eager=True, callback=validate_label, help='A label to refer to this code')
@click.option('--description',is_eager=True , callback=validate_description, help='A human-readable description of this code')
@click.option('--is-local', is_eager=True, callback=validate_local, help='True or False; if True, then you have to provide a folder with files that will be stored in AiiDA and copied to the remote computers for every calculation submission. if True the code is just a link to a remote computer and an absolute path there')
@click.option('--input-plugin', callback=validate_input_plugin, help='A string of the default input plugin to be used with this code that is recognized by the CalculationFactory. Use he verdi calculation plugins command to get the list of existing plugins')
@click.option('--code-folder', callback=validate_code_folder, help='For local codes: The folder on your local computer in which there are files to be stored in the AiiDA repository and then copied over for every submitted calculation')
@click.option('--code-rel-path', callback=validate_code_rel_path, help='The relative path of the executable file inside the folder entered in the previous step or in --code-folder')
@click.option('--computer', callback=validate_computer, help='The name of the computer on which the code resides as stored in the AiiDA database')
@click.option('--remote-abs-path', callback=validate_code_remote_path, help='The (full) absolute path on the remote machine')
@click.option('--prepend-text', callback=validate_prepend_text, help='Text to prepend to each command execution. FOR INSTANCE, MODULES TO BE LOADED FOR THIS CODE. This is a multiline string, whose content will be appended inside the submission script after the real execution of the job. It is your responsibility to write proper bash code!')
@verdic_options.non_interactive(is_eager=True)
def setup(label, description, is_local, input_plugin, code_folder, code_rel_path, computer, remote_abs_path, prepend_text, non_interactive):
    from aiida.common.exceptions import ValidationError

    set_params = CodeInputValidationClass()

    set_params.ask()

    code = set_params.create_code()

    # Enforcing the code to be not hidden.
    code._reveal()

    try:
        code.store()
    except ValidationError as e:
        print "Unable to store the computer: {}. Exiting...".format(e.message)
        sys.exit(1)

    print "Code '{}' successfully stored in DB.".format(code.label)
    print "pk: {}, uuid: {}".format(code.pk, code.uuid)
