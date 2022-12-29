import json
from pathlib import PosixPath
from typing import List, Dict

import shitlist


class Config:
    ignore_directories: List[str]
    deprecated_code: List[str]
    usage: Dict[str, List[str]]

    def __init__(
            self,
            deprecated_code: List[str] = [],
            usage: Dict[str, List[str]] = dict(),
            removed_usages: Dict[str, List[str]] = dict(),
            successfully_removed_things: List[str] = [],
            ignore_directories: List[str] = []
    ):
        self.deprecated_code = deprecated_code
        self.usage = usage
        self.removed_usages = removed_usages
        self.successfully_removed_things = successfully_removed_things
        self.ignore_directories = ignore_directories

    @staticmethod
    def from_file(path: str) -> 'Config':
        with open(path, 'r') as f:
            return Config(
                **json.load(f)
            )

    @staticmethod
    def from_path(path: PosixPath, ignore_directories: List[str] = []) -> 'Config':
        deprecated_code = shitlist.gen_for_path(path, ignore_directories=ignore_directories)
        usage = shitlist.find_usages(path, deprecated_code, ignore_directories=ignore_directories)

        return Config(
            deprecated_code=deprecated_code,
            usage=usage
        )

    def __eq__(self, other: 'Config'):
        return (
                self.deprecated_code == other.deprecated_code and
                self.usage == other.usage and
                self.removed_usages == other.removed_usages and
                self.successfully_removed_things == other.successfully_removed_things
        )

    def __dict__(self):
        return dict(
            ignore_directories=self.ignore_directories,
            deprecated_code=self.deprecated_code,
            usage=self.usage,
            removed_usages=self.removed_usages,
            successfully_removed_things=self.successfully_removed_things,
        )

    def __repr__(self):
        return f'Config({self.__dict__()})'

    def write(self, path):
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(self.__dict__(), file, ensure_ascii=False, indent=4)
            file.write('\n')
            file.flush()
