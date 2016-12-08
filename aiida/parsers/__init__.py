# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1"
__authors__ = "The AiiDA team."


def ParserFactory(module):
    """
    Return a suitable Parser subclass.
    """
    from aiida.common.ep_pluginloader import load_plugin
    return load_plugin('parsers')
