import ast
import enum
import logging
import os
from pathlib import PosixPath
from typing import List, Callable, Optional

from shitlist.config import Config
from shitlist.decorator_use_collector import DecoratorUseCollector
from shitlist.deprecated_thing_use_collector import DeprecatedThingUseCollector

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


def gen_for_path(
        root_path: PosixPath,
        ignore_directories=[]
):
    result = set()
    walker = TreeWalker(
        root_dir=root_path,
        ignore_directories=ignore_directories
    )

    while walker.has_next:
        path = walker.next_file()
        module_name = path.stem
        collector = DecoratorUseCollector(modulename=module_name)
        with open(path, 'r') as f:
            collector.visit(ast.parse(f.read()))

        module_relative_path = str(path).replace(str(root_path) + '/', '')
        if '__init__' in module_relative_path:
            module_relative_path = module_relative_path.replace('/__init__.py', '')
        module_relative_path = module_relative_path.replace('.py', '').replace('/', '.')
        result.update([f'{module_relative_path}::{thing}' for thing in collector.nodes_with_decorators])

    return sorted(list(result))


def test(existing_config: Config, new_config: Config):
    for thing in existing_config.deprecated_things:
        exiting_usages = set(existing_config.usage.get(thing, []))
        new_usages = set(new_config.usage.get(thing, []))
        dif = new_usages.difference(exiting_usages)
        if len(dif) > 0:
            raise DeprecatedException(f'Deprecated function {thing}, has new usages {dif}')


class TreeWalker:
    has_next: bool

    def __init__(self, root_dir: PosixPath, ignore_directories: List[str] = []):
        self.root_dir = root_dir
        self._walker = os.walk(root_dir)
        self._current_dir = None
        self._current_files = []
        self.has_next = True
        self.ignore_directories: List[PosixPath] = [root_dir / d for d in ignore_directories]

        self._gen_next()

    def _gen_next(self):
        try:
            self._current_dir, _, files = next(self._walker)
            self._current_files = [f for f in files if f[-3:] == '.py'] #TODO could error on short named files
            if not self._current_files or self.directory_should_be_ignored(self._current_dir):
                self._gen_next()
        except StopIteration:
            self.has_next = False

    def next_file(self) -> Optional[PosixPath]:
        if self.has_next:
            next_file = self._current_files.pop()
            full_path = PosixPath(self._current_dir) / next_file

            if len(self._current_files) == 0:
                self._gen_next()

            return full_path

    def directory_should_be_ignored(self, dir) -> bool:
        return any([True for ig_dir in self.ignore_directories if str(ig_dir) in dir])


def find_usages(
        root_path: PosixPath,
        deprecated_things: List[str],
        ignore_directories=[]
):
    result = {}
    walker = TreeWalker(
        root_dir=root_path,
        ignore_directories=ignore_directories
    )

    while walker.has_next:
        path = walker.next_file()
        module_name = path.stem
        relative_path = str(path).replace(f'{root_path}/', '')
        if module_name == '__init__':
            relative_path = relative_path.replace('/__init__.py', '')

        package = relative_path.replace('.py', '').replace('/', '.')

        for thing in deprecated_things:
            module, _, function_name = thing.rpartition('::')
            module_package = module.split('.')[0]
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
                result[thing] = [f'{package}::{u}' for u in collector.used_at]
    return result


def update(existing_config: Config, new_config: Config):
    merged_config = Config(
        deprecated_things=new_config.deprecated_things,
        usage=new_config.usage,
        ignore_directories=existing_config.ignore_directories
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
