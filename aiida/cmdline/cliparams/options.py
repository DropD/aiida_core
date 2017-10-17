"""Common click options for verdi commands"""
import click

from aiida.cmdline.cliparams.paramtypes.plugin import PluginParam
from aiida.cmdline.cliparams.paramtypes.computer import ComputerParam


class OverridableOption(object):
    """
    Wrapper around click option that increases reusability

    Click options are reusable already but sometimes it can improve the user interface to for example customize a help message
    for an option on a per-command basis. Sometimes the option should be prompted for if it is not given. On some commands an option
    might take any folder path, while on another the path only has to exist.

    Overridable options store the arguments to click.option and only instanciate the click.Option on call, kwargs given to ``__call__``
    override the stored ones.

    Example::

        FOLDER = OverridableOption('--folder', type=click.Path(file_okay=False), help='A folder')

        @click.command()
        @FOLDER(help='A folder, will be created if it does not exist')
        def ls_or_create(folder):
            click.echo(os.listdir(folder))

        @click.command()
        @FOLDER(help='An existing folder', type=click.Path(exists=True, file_okay=False, readable=True)
        def ls(folder)
            click.echo(os.listdir(folder))
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


FORCE = OverridableOption('-f', '--force', is_flag=True, help='Do not ask for confirmation')
LABEL = OverridableOption('-L', '--label', help='short text to be used as a label')
DESCRIPTION = OverridableOption('-D', '--description', help='(text) description')
INPUT_PLUGIN = OverridableOption('--input-plugin', help='input plugin string', type=PluginParam(category='calculations'))

REMOTE_ABS_PATH = OverridableOption('--remote-abs-path', type=click.Path(file_okay=True),
                                    help=('[if --installed]: The (full) absolute path on the remote ' 'machine'))

PREPEND_TEXT = OverridableOption('--prepend-text', type=str, default='',
                                 help='Text to prepend to each command execution. FOR INSTANCE, MODULES TO BE LOADED FOR THIS CODE. This '
                                      'is a multiline string, whose content will be prepended inside the submission script after the real '
                                      'execution of the job. It is your responsibility to write proper bash code!')

APPEND_TEXT = OverridableOption('--append-text', type=str, default='',
                                help='Text to append to each command execution. This is a multiline string, whose content will be appended '
                                     'inside the submission script after the real execution of the job. It is your responsibility to write '
                                     'proper bash code!')

DRY_RUN = OverridableOption('--dry-run', is_flag=True, is_eager=True,
                            help='do not commit to database or modify configuration files')

NON_INTERACTIVE = OverridableOption('--non-interactive', is_flag=True, is_eager=True,
                                    help='noninteractive mode: never prompt the user for input')

COMPUTER = OverridableOption('-C', '--computer', type=ComputerParam(),
                              help=('The name of the computer as stored in the AiiDA database'))
