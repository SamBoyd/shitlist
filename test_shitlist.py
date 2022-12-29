import ast

from shitlist.deprecated_code_use_collector import DeprecatedCodeUseCollector

collector = DeprecatedCodeUseCollector(deprecated_code='', modulename='shitlist', package='shitlist')

with open('tests/example_file.py', 'r') as f:
    collector.visit(ast.parse(f.read()))
