import ast
import enum
import importlib
import logging
import os
import pkgutil
import sys
from typing import List, Callable, Dict
import logging
from pathlib import Path, PosixPath

import click

from shitlist.deprecated_thing_use_collector import DeprecatedThingUseCollector
from shitlist.decorator_use_collector import DecoratorUseCollector
from shitlist.foo import Config

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)


class DeprecatedException(Exception):
    pass


class ErrorLevel(enum.Enum):
    error = 'error'
    warn = 'warn'


usages = []
error_level = ErrorLevel.error


class WrongTypeError(Exception):
    pass


def get_func_name(func: Callable):
    filepath = func.__code__.co_filename
    filepath = filepath.replace(ROOT_DIR, '')
    func_name = func.__qualname__
    return f'{filepath}::{func_name}'


def deprecate(func):
    # wrap a function
    if type(func).__name__ == 'function':
        def wrapper():
            if get_func_name(func) not in usages:
                if error_level == ErrorLevel.error:
                    raise RuntimeError()
                else:
                    func_name = func.__qualname__
                    logger.info(
                        f'function {func_name} is registered on a shitlist and therefore should not'
                        f' be used by new code'
                    )
            func()

        wrapper.shitlist_deprecate = True
        wrapper.wrapped_function = get_func_name(func)

        return wrapper
    else:
        raise WrongTypeError()


def gen_for_path(root_path: str):
    result = set()
    walker = os.walk(root_path)

    while True:
        try:
            dir, subdirs, files = next(walker)
            # print(f'Looking at files under: {dir}')
            for file in [f for f in files if f[-3:] == '.py']:
                print(f'looking at file: {dir}/{file}')
                path = Path(f'{dir}/{file}')
                module_name = path.stem
                collector = DecoratorUseCollector(modulename=module_name)
                with open(path, 'r') as f:
                    collector.visit(ast.parse(f.read()))

                module_relative_path = str(path).replace(root_path + '/', '')
                if '__init__' in module_relative_path:
                    module_relative_path = module_relative_path.replace('/__init__.py', '')
                module_relative_path = module_relative_path.replace('.py', '').replace('/', '.')
                result.update([f'{module_relative_path}::{thing}' for thing in collector.nodes_with_decorators])
        except StopIteration:
            break

    return sorted(list(result))


def test(existing_config: Config, new_config: Config):
    for thing in existing_config.deprecated_things:
        exiting_usages = set(existing_config.usage.get(thing, []))
        new_usages = set(new_config.usage.get(thing, []))
        dif = new_usages.difference(exiting_usages)
        if len(dif) > 0:
            raise DeprecatedException(f'Deprecated function {thing}, has new usages {dif}')


def find_usages(root_path: str, deprecated_things: List[str]):
    result = {}
    walker = os.walk(root_path)

    while True:
        try:
            dir, subdirs, files = next(walker)
            for file in [f for f in files if f[-3:] == '.py']:
                print(f'looking at file: {dir}/{file}')
                path = Path(f'{dir}/{file}')
                module_name = path.stem
                relative_path = str(path).replace(f'{root_path}/', '')
                if module_name == '__init__':
                    relative_path = relative_path.replace('/__init__.py', '')

                package = relative_path.replace('.py', '').replace('/', '.')

                for thing in deprecated_things:
                    module, _, function_name = thing.rpartition('::')
                    module_package = module.split('.')[0]
                    print(f'searching for {module_package}::{function_name}')
                    collector = DeprecatedThingUseCollector(
                        deprecated_thing=function_name,
                        modulename=module,
                        package=module_package
                    )

                    with open(path, 'r') as f:
                        collector.visit(ast.parse(f.read()))

                    if thing in result:
                        result[thing].extend([f'{package}::{u}' for u in collector.used_at])
                    else:
                        result[thing] = collector.used_at
        except StopIteration:
            break

    return result


def update(existing_config: Config, new_config: Config):
    merged_config = Config(
        deprecated_things=new_config.deprecated_things,
        usage=new_config.usage,
    )

    merged_config.successfully_removed_things = [
        t for t in existing_config.deprecated_things if t not in new_config.deprecated_things
    ]

    for thing, new_usage in new_config.usage.items():
        if thing in existing_config.usage:
            existing_usage = existing_config.usage[thing]
            removed_usages = [u for u in existing_usage if u not in new_usage]
            if removed_usages:
                merged_config.removed_usages[thing] = list(removed_usages)

    return merged_config
