import json
from typing import List, Dict


class Config:
    deprecated_things: List[str]
    usage: Dict[str, List[str]]

    def __init__(
            self,
            deprecated_things: List[str],
            usage: Dict[str, List[str]]
    ):
        self.usage = usage
        self.deprecated_things = deprecated_things

    @staticmethod
    def from_file(path: str) -> 'Config':
        with open(path, 'r') as f:
            file_contents = json.load(f)
            return Config(
                deprecated_things=file_contents['deprecated_things'],
                usage=file_contents['usage']
            )
