import click
from click_plugins import with_plugins
from pkg_resources import iter_entry_points


@with_plugins(iter_entry_points('aiida.cmdline.verdi'))
@click.group()
@click.option('-p', '--profile', metavar='PROFILENAME')
def verdic(profile):
    """
    The commandline interface to AiiDA
    """
    from aiida.backends import settings as settings_profile
    # We now set the internal variable, if needed
    if profile is not None:
        settings_profile.AIIDADB_PROFILE = profile
    # I set the process to verdi
    settings_profile.CURRENT_AIIDADB_PROCESS = "verdi"
