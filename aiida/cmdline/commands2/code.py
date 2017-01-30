import sys
import click

from aiida.cmdline import verdic_options
from aiida.cmdline.verdic_utils import load_dbenv_if_not_loaded, aiida_dbenv, prompt_help_loop, prompt_with_help
from aiida.cmdline.verdic_types.code import CodeArgument

@click.group()
def code():
    """
    manage codes in your AiiDA database.
    """

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
    from aiida.cmdline.verdic_utils import print_list_res
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

@code.command()
@click.argument('code', metavar='CODE', type=CodeArgument())
def show(code):
    """
    Show information on a given code
    """
    from aiida.cmdline.verdic_utils import get_code

    code = get_code(code)
    print code.full_text_info

def validate_local(ctx, param, value):
    if value in [True, 'True', 'true', 'T']:
        return True, True
    elif value in [False, 'False', 'false', 'F']:
        return True, False
    else:
        return False, None

@aiida_dbenv
def input_plugin_list():
    from aiida.common.pluginloader import existing_plugins
    from aiida.orm.calculation.job import JobCalculation
    return [p.rsplit('.', 1)[0] for p in existing_plugins(JobCalculation, 'aiida.orm.calculation.job')]

def validate_input_plugin(ctx, param, value):
    pluginlist = input_plugin_list()
    if value in pluginlist:
        return True, value
    else:
        return False, None

def validate_path(prefix_opt=None, is_abs=False, **kwargs):
    def decorated_validator(ctx, param, value):
        from os import path
        from os.path import expanduser, isabs
        path_t = click.Path(**kwargs)
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
                return False, value
            else:
                return True, value
        return decorated_validator
    return decorator

def validate_code_folder(ctx, param, value):
    from os.path import expanduser
    path_t = click.Path(exists=True, file_okay=False, readable=True, resolve_path=True)
    if ctx.params.get('is_local'):
        if value:
            try:
                value = expanduser(value)
                value = path_t.convert(value, param, ctx)
                result = True, value
            except click.BadParameter as e:
                click.echo(e.format_message(), err=True)
                result = False, value
        else:
            return False, value
    else:
        return True, value
    return result

# ~ @prompt_help_loop(prompt='Relative path of the executable')
# ~ @validate_path(prefix_opt='code_folder', exists=True, dir_okay=False)
@required_if_opt(opt='is_local')
def validate_code_rel_path(ctx, param, value):
    return value

@prompt_help_loop(prompt='Remote computer name')
@required_if_opt(opt='is_local', opt_value=False)
def validate_computer(ctx, param, value):
    return value

@prompt_help_loop(prompt='Remote absolute path')
# ~ @validate_path(is_abs=True, dir_okay=False)
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
@click.option('--label', is_eager=True, callback=prompt_with_help(prompt='Label'), help='A label to refer to this code')
@click.option('--description',is_eager=True , callback=prompt_with_help(prompt='Description'), help='A human-readable description of this code')
@click.option('--is-local', is_eager=True, callback=prompt_with_help(prompt='Local', callback=validate_local), help='True or False; if True, then you have to provide a folder with files that will be stored in AiiDA and copied to the remote computers for every calculation submission. if True the code is just a link to a remote computer and an absolute path there')
@click.option('--input-plugin', callback=prompt_with_help(prompt='Default input plugin', suggestions=input_plugin_list), help='A string of the default input plugin to be used with this code that is recognized by the CalculationFactory. Use he verdi calculation plugins command to get the list of existing plugins')
@click.option('--code-folder', callback=prompt_with_help(prompt='Folder containing the code', callback=validate_code_folder), help='For local codes: The folder on your local computer in which there are files to be stored in the AiiDA repository and then copied over for every submitted calculation')
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
