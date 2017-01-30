import click
from click_spinner import spinner as cli_spinner

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

@aiida_dbenv
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

def default_callback(ctx, param, value):
    return bool(value), value

def single_value_prompt(ctx, param, value, prompt=None, default=None, callback=default_callback, suggestions=None, **kwargs):
    """
    prompt for a single value on the commandline

    :param ctx: context object, passed by click on callback
    :param param: parameter object, passed by click on callback
    :param value: parameter value, passed by click on callback
    :kwarg prompt: the prompt displayed on the input line
    :kwarg default: the default input (pressing return on an empty line)
    :kwarg suggestions: callable that returns a list of suggestions
    :kwargs callback: callable that returns (valid, value) where valid is True if value is valid and value is the (converted) input value
    :return: value as converted by callback
    """
    import pprint
    keep_prompting = True
    _help = param.help or 'invalid input'
    if suggestions:
        _help += '\none of:\n' + pprint.pformat(suggestions(), indent=3)
    while keep_prompting:
        inp = click.prompt(prompt, default=default)
        if inp == '?':
            click.echo(_help)
        else:
            valid, converted_value = callback(ctx, param, inp)
            if valid:
                return converted_value

def multi_line_prompt(ctx, param, value, header=True, **kwargs):
    """
    prompt for multiple lines of input on the commandline

    :kwarg bool header: controls if the header message should be printed
    :return: list of lines
    """
    '''print header if requested'''
    if header:
        click.echo('-------------------------------------------------')
        click.echo('| multiline input, ? for help, \\quit to accept |')
        click.echo('-------------------------------------------------')
    lines = []
    keep_prompting = True
    _help = param.help or 'multline text input'
    while keep_prompting:
        line = click.prompt('line {:<3}'.format(len(text)), default='', show_default=False)
        if line == '\\quit':
            break
        if line == '\\restart':
            click.echo('-------------------------------------------------')
            lines = []
        elif line == '?':
            click.echo(_help)
            click.echo('\\quit to conclude and accept, \\restart to start over')
            click.echo('-------------------------------------------------')
        else:
            lines.append(line)
        return lines
def prompt_with_help(prompt=None, default=None, suggestions=None, callback=default_callback, ni_callback=None, prompt_loop=single_value_prompt, **kwargs):
    """
    create a callback function to prompt for input which displays help if '?' is entered

    :kwarg prompt: the prompt displayed on the input line
    :kwarg default: the default input (pressing return on an empty line), passed to the prompt_loop callback
    :kwarg suggestions: callable that returns a list of suggestions, passed to prompt_loop
    :kwargs callback: callable that returns (valid, value) where valid is True if value is valid and value is the (converted) input value
    :kwargs ni_callback: alternative callback to be used if --non-interactive is set
    :kwargs prompt_loop: callback that prompts the commandline for input
    :return: the value as converted by callback or ni_callback if given or as entered on the commandline if not or as returned by prompt_loop if value was not considered valid
    """
    def prompt_callback(ctx, param, value):
        '''gather relevant context info'''
        non_interactive = ctx.params.get('non_interactive')
        debug = ctx.params.get('debug')

        '''print debug info if flag is set'''
        if debug:
            click.echo('context: ' + str(ctx))
            click.echo('parameter: ' + str(param))
            click.echo('value: ' + repr(value))

        '''validate and optionally convert'''
        if non_interactive and ni_callback:
            valid_input, value = ni_callback(ctx, param, value)
        elif callback:
            valid_input, value = callback(ctx, param, value)
        else:
            valid_input = bool(value)

        '''to prompt or not to prompt'''
        if not valid_input and not non_interactive:
            '''prompting necessary'''
            value = prompt_loop(ctx, param, value, prompt=prompt, default=default, suggestions=suggestions, callback=callback, **kwargs)
        '''more debug info'''
        if debug:
            click.echo('recieved: ' + str(value))
        return value
    return prompt_callback

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

