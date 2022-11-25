import json
from typing import List, Dict


class Config:
    deprecated_things: List[str]
    usage: Dict[str, List[str]]

    def __init__(
            self,
            deprecated_things: List[str],
            usage: Dict[str, List[str]],
            removed_usages: Dict[str, List[str]] = dict(),
            successfully_removed_things: List[str] = []
    ):
        self.deprecated_things = deprecated_things
        self.usage = usage
        self.removed_usages = removed_usages
        self.successfully_removed_things = successfully_removed_things

    @staticmethod
    def from_file(path: str) -> 'Config':
        with open(path, 'r') as f:
            file_contents = json.load(f)
            return Config(
                deprecated_things=file_contents['deprecated_things'],
                usage=file_contents['usage']
            )

    def __eq__(self, other: 'Config'):
        return (
                self.deprecated_things == other.deprecated_things and
                self.usage == other.usage and
                self.removed_usages == other.removed_usages and
                self.successfully_removed_things == other.successfully_removed_things
        )

    def __dict__(self):
        return dict(
            deprecated_things=self.deprecated_things,
            usage=self.usage,
            removed_usages=self.removed_usages,
            successfully_removed_things=self.successfully_removed_things
        )

    def __repr__(self):
        return f'Config({self.__dict__()})'
