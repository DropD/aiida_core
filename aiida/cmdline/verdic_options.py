import click

from  aiida.backends.profile import (BACKEND_DJANGO, BACKEND_SQLA)

backend = click.option('--backend', type=click.Choice([BACKEND_DJANGO, BACKEND_SQLA],),
                       help='backend choice')

email = click.option('--email', metavar=

import click


@click.command('setup', short_help='Setup an AiiDA profile')
@click.argument('profile', default='', metavar='PROFILE', type=str)#, help='Profile Name to create/edit')
@click.option('--only-config', is_flag=True, help='Do not create a new user')
@click.option('--non-interactive', is_flag=True, help='never prompt the user for input, read values from options')
@click.option('--backend', type=click.Choice(['django', 'sqlalchemy']), help='backend choice (ignored without --non-interactive)')
@click.option('--email', metavar='EMAIL', type=str, help='valid email address for the user (ignored without --non-interactive)')
@click.option('--db_host', metavar='HOSTNAME', type=str, help='database hostname (ignored without --non-interactive)')
@click.option('--db_port', metavar='PORT', type=int, help='database port (ignored without --non-interactive)')
@click.option('--db_name', metavar='DBNAME', type=str, help='database name (ignored without --non-interactive)')
@click.option('--db_user', metavar='DBUSER', type=str, help='database username (ignored without --non-interactive)')
@click.option('--db_pass', metavar='DBPASS', type=str, help='password for username to access the database (ignored without --non-interactive)')
@click.option('--first-name', metavar='FIRST', type=str, help='your first name (ignored without --non-interactive)')
@click.option('--last-name', metavar='LAST', type=str, help='your last name (ignored without --non-interactive)')
@click.option('--institution', metavar='INSTITUTION', type=str, help='your institution (ignored without --non-interactive)')
@click.option('--no-password', is_flag=True, help='do not set a password (--non-interactive fails otherwise)')
@click.option('--repo', metavar='PATH', type=click.Path(), help='data file repository (ignored without --non-interactive)')
