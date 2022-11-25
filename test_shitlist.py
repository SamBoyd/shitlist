import ast

from shitlist.deprecated_thing_use_collector import DeprecatedThingUseCollector

collector = DeprecatedThingUseCollector(deprecated_thing='', modulename='shitlist', package='shitlist')

with open('tests/example_file.py', 'r') as f:
    collector.visit(ast.parse(f.read()))
