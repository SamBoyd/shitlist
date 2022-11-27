import json
import logging
import os
from pathlib import PosixPath

import click

import shitlist

logger = logging.getLogger(__name__)


class NoConfigFileException(Exception):
    pass

@click.group()
def init_cli():
    pass


@init_cli.command()
def init():
    """Initialize the shitlist coniguration file

    Creates the .shitlist file in the project root directory
    \f
    """
    if os.path.exists('.shitlist'):
        logger.info('Initialized file already exists')
        return

    click.echo("Initializing config file in .shitlist")

    cwd = os.getcwd()

    config = shitlist.Config()
    config.write('.shitlist')


@click.group()
def test_cli():
    pass


@test_cli.command()
def test():
    """Test new usages of deprecated code

    The test fails if you introduce new usages of deprecated code
    """
    if not os.path.exists('.shitlist'):
        logger.info('Cannot test there is no config file present')
        raise NoConfigFileException()

    existing_config = shitlist.Config.from_file('.shitlist')

    cwd = PosixPath(os.getcwd())
    new_config = shitlist.Config.from_path(
        cwd,
        ignore_directories=existing_config.ignore_directories
    )

    shitlist.test(
        existing_config=existing_config,
        new_config=new_config
    )


@click.group()
def update_cli():
    pass


@update_cli.command()
def update():
    """Update the config with removed usages

    Update the shitlist config with any newly deprecated code
    """
    if not os.path.exists('.shitlist'):
        logger.info('Cannot test there is no config file present')
        raise NoConfigFileException()

    existing_config = shitlist.Config.from_file('.shitlist')

    cwd = PosixPath(os.getcwd())

    new_config = shitlist.Config.from_path(
        cwd,
        ignore_directories=existing_config.ignore_directories
    )

    shitlist.test(
        existing_config=existing_config,
        new_config=new_config
    )

    merged_config = shitlist.update(
        existing_config=existing_config,
        new_config=new_config
    )

    merged_config.write('.shitlist')


cli = click.CommandCollection(sources=[init_cli, test_cli, update_cli])


def main():
    cli()
