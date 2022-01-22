import os
import sys
import click
from flask.cli import with_appcontext


@click.command('test')
@click.argument('directory', nargs=1)
@with_appcontext
def test(directory):
    '''Run tests with coverage for specified directory'''

    if sys.prefix == sys.base_prefix:
        print('You must first activate the virtual environment')

    else:
        os.system(f'pytest --cov={directory} -v')
        os.system('rm .coverage')


@click.command('prune-expired-tokens')
@with_appcontext
def prune_expired_tokens():
    '''Remove tokens from JWTBlocklist that are expired'''
    print('This command has not yet been set up')
    pass
