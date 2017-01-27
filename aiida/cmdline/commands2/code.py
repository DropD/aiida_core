import click

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

@code.command()
@click.option('-c', '--computer', help='filter codes for a computer')
@click.option('-p', '--plugin', help='filter codes for a plugin')
@click.option('-A', '--all-users', help='show codes of all users')
@click.option('-o', '--show-owner', is_flag=True, help='show owner information')
@click.option('-a', '--all-codes', is_flag=True, help='show hidden codes')
def list(computer, plugin, all_users, show_owner, all_codes):
    """
    List available codes
    """
    computer_filter = parsed_args.computer
    plugin_filter = parsed_args.plugin
    reveal_filter = parsed_args.all_codes

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
    print "# (use 'verdi code show CODEID' to see the details)"
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
        self.print_list_res(qb, show_owner)

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
        self.print_list_res(qb, show_owner)

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
        self.print_list_res(qb, show_owner)

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

@code.command()
@click.argument('code', metavar='CODE', type=click.Choice(['1', '2']))
def show(code):
    code = get_code(code)
    print code.full_text_info
