"""Reusable click arguments for verdi commands"""
import click

from aiida.cmdline.cliparams.paramtypes.code import CodeParam


class OverridableArgument(object):
    """
    Reusablility wrapper for click.argument

    Analog to :py:class:`aiida.cmdline.cliparams.options.OverridableOption`

    Once defined, the option can be reused with a consistent name and sensible defaults while
    other details can be customized on a per-command basis

    Example::

        @click.command()
        @NODE_ID(metavar='<NODE TO BE INSPECTED>')
        def look_at(node_id):
            # find and inspect node with

        @click.command()
        @NODE_ID('node_id_list', nargs=-1, metavar='NODE-LIST')
        def display_connections(node_id_list):
            # find all the nodes and display their connections
    """
    def __init__(self, *args, **kwargs):
        """
        store defaults
        """
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        """
        Override kwargs and return click argument
        """
        kw_copy = self.kwargs.copy()
        kw_copy.update(kwargs)
        self.args += args
        return click.argument(*self.args, **kw_copy)


CODE = OverridableArgument('code', metavar='CODE', type=CodeParam())
