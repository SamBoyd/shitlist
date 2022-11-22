import ast
import enum
import importlib
import logging
import os
import pkgutil
import sys
from typing import List, Callable
import logging
from pathlib import Path, PosixPath

import click
from shitlist.decorator_use_collector import DecoratorUseCollector

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)


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
                result.update([f'{module_relative_path}::{thing}' for thing in collector.nodes_with_decorators])
        except StopIteration:
            break

    return sorted(list(result))
