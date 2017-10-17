# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import sys
import textwrap

from aiida.cmdline.cliparams.templates import env


def print_node_summary(node):
    from tabulate import tabulate

    table = []
    table.append(["type", node.__class__.__name__])
    table.append(["pk", str(node.pk)])
    table.append(["uuid", str(node.uuid)])
    table.append(["label", node.label])
    table.append(["description", node.description])
    table.append(["ctime", node.ctime])
    table.append(["mtime", node.mtime])

    try:
        computer = node.get_computer()
    except AttributeError:
        pass
    else:
        if computer is not None:
            table.append(["computer",
                          "[{}] {}".format(node.get_computer().pk,
                                           node.get_computer().name)])
    try:
        code = get_code()
    except AttributeError:
        pass
    else:
        if code is not None:
            table.append(["code", code.label])

    print(tabulate(table))

def print_node_info(node, print_summary=True):
    from tabulate import tabulate
    from aiida.backends.utils import get_log_messages
    from aiida.orm.calculation.work import WorkCalculation

    if print_summary:
        print_node_summary(node)

    table_headers = ['Link label', 'PK', 'Type']

    table = []
    print "##### INPUTS:"
    for k, v in node.get_inputs_dict().iteritems():
        if k == 'code': continue
        table.append([k, v.pk, v.__class__.__name__])
    print(tabulate(table, headers=table_headers))

    table = []
    print "##### OUTPUTS:"
    for k, v in node.get_outputs(also_labels=True):
        table.append([k, v.pk, v.__class__.__name__])
    print(tabulate(table, headers=table_headers))

    log_messages = get_log_messages(node)
    if log_messages:
        print "##### LOGS:"
        print ("There are {} log messages for this calculation".format(len(log_messages)))
        if isinstance(node, WorkCalculation):
            print ("Run 'verdi work report {}' to see them".format(node.pk))
        else:
            print ("Run 'verdi calculation logshow {}' to see them".format(node.pk))

def render_warning(msg, width=35):
    warning_tpl = env.get_template('warning.tpl')
    msg_lines = textwrap.wrap(msg, width-4)
    return warning_tpl.render(msg=msg_lines, width=width)


def get_code(code_id):
    """
    Get a Computer object with given identifier, that can either be
    the numeric ID (pk), or the label (if unique).

    .. note:: Since all command line arguments get converted to string types, we
        cannot assess the intended type (an integer pk or a string label) from the
        type of the variable code_id. If the code_id can be converted into an integer
        we will assume the value corresponds to a pk. This means, however, that if there
        would be another code, with a label directly equivalent to the string value of that
        pk, that this code can not be referenced by its label, as the other code, corresponding
        to the integer pk, will get matched first.
    """
    from aiida.common.exceptions import NotExistent, MultipleObjectsError, InputValidationError
    from aiida.orm import Code as AiidaOrmCode

    try:
        pk = int(code_id)
        try:
            return AiidaOrmCode.get(pk=pk)
        except (NotExistent, MultipleObjectsError, InputValidationError) as e:
            print >> sys.stderr, e.message
            sys.exit(1)
    except ValueError:
        try:
            return AiidaOrmCode.get_from_string(code_id)
        except (NotExistent, MultipleObjectsError) as e:
            print >> sys.stderr, e.message
            sys.exit(1)
