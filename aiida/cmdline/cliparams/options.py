import click


class overridable_option(object):
    """
    wrapper around click option that allows to store the name
    and some defaults but also to override them later, for example
    to change the help message for a certain command.
    """
    def __init__(self, *args, **kwargs):
        """
        store the defaults.
        """
        self.args = args
        self.kwargs = kwargs

    def __call__(self, **kwargs):
        """
        override kwargs (no name changes) and return option
        """
        kw_copy = self.kwargs.copy()
        kw_copy.update(kwargs)
        return click.option(*self.args, **kw_copy)


FORCE = overridable_option('-f', '--force', is_flag=True, help='Do not ask for confirmation')
