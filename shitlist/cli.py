import logging
import os
from pathlib import PosixPath

import click

import shitlist

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

config_filepath = '.shitlist'


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
    if os.path.exists(config_filepath):
        logger.info('Initialized file already exists')
        return

    click.echo(f"Initializing config file in {config_filepath}")

    cwd = os.getcwd()

    config = shitlist.Config()
    config.write(config_filepath)


@click.group()
def test_cli():
    pass


@test_cli.command()
def test():
    """Test new usages of deprecated code

    The test fails if you introduce new usages of deprecated code
    """
    if not os.path.exists(config_filepath):
        logger.info('Cannot test there is no config file present')
        raise NoConfigFileException()

    existing_config = shitlist.Config.from_file(config_filepath)

    cwd = PosixPath(os.getcwd())
    new_config = shitlist.Config.from_path(
        cwd,
        ignore_directories=existing_config.ignore_directories
    )

    shitlist.test(
        existing_config=existing_config,
        new_config=new_config
    )

    logger.info('Successfully tested deprecated code')

    if [dc for dc in new_config.deprecated_code if dc not in existing_config.deprecated_code]:
        logger.info(
            'Warning: there is newly deprecated code not represented in config. '
            'Run `shitlist update`'
        )


@click.group()
def update_cli():
    pass


@update_cli.command()
def update():
    """Update the config with removed usages

    Update the shitlist config with any newly deprecated code
    """
    if not os.path.exists(config_filepath):
        logger.info('Cannot test there is no config file present')
        return

    existing_config = shitlist.Config.from_file(config_filepath)

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

    merged_config.write(config_filepath)


@click.group()
def progress_cli():
    pass


@progress_cli.command()
def progress():
    """Display deprecated code burn down table"""

    if not os.path.exists(config_filepath):
        logger.info('Cannot test there is no config file present')
        return

    config = shitlist.Config.from_file(config_filepath)

    progress_map = {
        dc: (len(config.removed_usages.get(dc, [])), len(config.usage[dc]) + len(config.removed_usages.get(dc, [])))
        for dc in config.deprecated_code
    }

    logger.info('Progress removing deprecated code:')

    for dc in config.deprecated_code:
        remaining, total = progress_map[dc]

        if total == 0:
            logger.info(f' 100%\t[##########]\t{dc}')
        else:
            out_of_ten = int((remaining / total) * 10)
            l = '#' * out_of_ten
            s = '-' * (10 - out_of_ten)
            logger.info(f' {out_of_ten * 10}%\t[{l}{s}]\t{dc}')


cli = click.CommandCollection(sources=[init_cli, test_cli, update_cli, progress_cli])


def main():
    cli()
