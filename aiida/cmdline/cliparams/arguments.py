import click

from aiida.cmdline.cliparams.paramtypes.code import CodeParam


class overridable_argument(object):
    """
    wrapper around click argument that allows for defaults to be stored for reuse
    and for some arguments to be overriden later.
    """
    def __init__(self, *args, **kwargs):
        """
        store defaults
        """
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        """
        override kwargs and return click argument
        """
        kw_copy = self.kwargs.copy()
        kw_copy.update(kwargs)
        self.args += args
        return click.argument(*self.args, **kw_copy)


CODE = overridable_argument('code', metavar='CODE', type=CodeParam())
