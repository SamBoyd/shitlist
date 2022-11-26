import json
import logging
import os

import click

import shitlist

logger = logging.getLogger(__name__)


@click.group()
def init_cli():
    pass


@init_cli.command()
def init():
    """Initialize the shitlist coniguration file

    Creates the .shitlist file in the project root directory
    \f
    """

    click.echo("Initializing config file in .shitlist")

    cwd = os.getcwd()
    deprecated_things = shitlist.gen_for_path(cwd)

    usages = shitlist.find_usages(cwd, deprecated_things)

    with open('.shitlist', 'w', encoding='utf-8') as file:
        data = dict(
            deprecated_things=deprecated_things,
            usage=usages
        )
        json.dump(data, file, ensure_ascii=False, indent=4)
        file.write('\n')
        file.flush()


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

    existing_config = shitlist.Config.from_file('.shitlist')

    cwd = os.getcwd()
    new_config = shitlist.Config(
        deprecated_things=shitlist.gen_for_path(cwd),
        usage={}
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
    existing_config = shitlist.Config.from_file('.shitlist')

    cwd = os.getcwd()

    new_config = shitlist.Config(
        deprecated_things=shitlist.gen_for_path(cwd),
        usage={}
    )

    shitlist.test(
        existing_config=existing_config,
        new_config=new_config
    )

    merged_config = shitlist.update(
        existing_config=existing_config,
        new_config=new_config
    )
    with open('.shitlist', 'w', encoding='utf-8') as file:
        json.dump(merged_config.__dict__(), file, ensure_ascii=False, indent=4)
        file.write('\n')
        file.flush()


cli = click.CommandCollection(sources=[init_cli, test_cli, update_cli])


def main():
    cli()
