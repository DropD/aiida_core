#-*- coding: utf8 -*-
"""
click parameter type for Plugins
"""
import click
from click_completion import startswith

from aiida.cmdline.dbenv_lazyloading import with_dbenv


class PluginParam(click.ParamType):
    """
    handle verification, completion for plugin arguments
    """
    name = 'aiida plugin'

    def __init__(self, category=None, available=True, *args, **kwargs):
        self.category = category
        self.must_available = available
        super(PluginParam, self).__init__(*args, **kwargs)
        from aiida.common import pluginloader
        self.get_all_plugins = self.get_plugins_for_cat(category)

    def get_possibilities(self, incomplete=''):
        """return a list of plugins starting with incomplete"""
        return [p for p in self.get_all_plugins() if startswith(p, incomplete)]

    def get_plugins_for_cat(self, category):
        """use entry points"""

        @with_dbenv
        def get_plugins():
            from aiida.common.pluginloader import all_plugins
            return all_plugins(category)
        return get_plugins

    def complete(self, ctx, incomplete):
        """return possible completions"""
        return [(p, '') for p in self.get_possibilities(incomplete=incomplete)]

    def get_missing_message(self, param):
        return 'Possible arguments are:\n\n' + '\n'.join(self.get_all_plugins())

    def convert(self, value, param, ctx):
        """check value vs. possible plugins, raising BadParameter on fail """
        if not value:
            raise click.BadParameter('plugin name cannot be empty')
        if self.must_available:
            pluginlist = self.get_possibilities()
            if param.default:
                pluginlist.append(param.default)
            if value not in pluginlist:
                raise click.BadParameter('{} is not a plugin for category {}'.format(value, self.category))
        return value
