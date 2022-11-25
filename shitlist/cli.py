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

    Initialize the .shitlist file in the project root directory
    \f

    :param click.core.Context ctx: Click context.
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
def cli2():
    pass


@cli2.command()
def cmd2():
    """Command on cli2"""


@click.group()
def test_cli():
    pass


@test_cli.command()
def test():
    """Test new usages of deprecated code
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


cli = click.CommandCollection(sources=[cli2, init_cli, test_cli])


def main():
    cli()
