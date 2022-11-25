import importlib
import os
from pathlib import PosixPath

import pytest
from hamcrest import assert_that, equal_to, has_items, contains_inanyorder, only_contains

import shitlist
from shitlist import deprecate

from tests import example_module


@shitlist.deprecate
def func_test():
    return 0


@deprecate
def another_func_test():
    return 1


def test_raises_if_not_function():
    with pytest.raises(shitlist.WrongTypeError):
        @shitlist.deprecate
        class TestClass:
            pass


def test_raises_runtime_error():
    with pytest.raises(RuntimeError) as e_info:
        @shitlist.deprecate
        def func():
            return 0

        func()


def test_passes_check(mocker):
    @shitlist.deprecate
    def func():
        return 0

    mocker.patch('shitlist.usages', new=['test_passes_check.<locals>.func'])

    func()


def test_generate_shitlist_for_path(pytestconfig):
    test_root = PosixPath(pytestconfig.rootpath)
    result = shitlist.gen_for_path(str(test_root.parent))

    expected_result = [
        'example_module::wrapped_1',
        'example_module::wrapped_2',
        'example_module.example_file::wrapped_3',
        'example_module.submodule::wrapped',
        'example_module.submodule.example_file::wrapped',
    ]

    assert_that(
        result,
        has_items(*expected_result)
    )


def test_shitlist_test_throws_an_exception_if_theres_a_new_usage_of_a_deprecated_thing():
    existing_config = {
        'deprecated_things': [
            'thing_1',
            'thing_2',
            'thing_3'
        ],
        'usage': {
            'thing_1': ['usage_1_of_thing_1', 'usage_2_of_thing_1'],
            'thing_2': ['usage_1_of_thing_2', 'usage_2_of_thing_2'],
            'thing_3': ['usage_1_of_thing_3', 'usage_2_of_thing_3'],
        }
    }

    new_config = {
        'deprecated_things': [
            'thing_1',
            'thing_2',
            'thing_3'
        ],
        'usage': {
            'thing_1': ['usage_1_of_thing_1', 'usage_2_of_thing_1'],
            'thing_2': ['usage_1_of_thing_2', 'usage_2_of_thing_2'],
            'thing_3': ['usage_1_of_thing_3', 'usage_2_of_thing_3', 'usage_3_of_thing_3'],
        }
    }

    with pytest.raises(shitlist.DeprecatedException):
        shitlist.test(
            existing_config=existing_config,
            new_config=new_config
        )


def test_shitlist_test_passes():
    existing_config = {
        'deprecated_things': [
            'thing_1',
            'thing_2',
            'thing_3'
        ],
        'usage': {
            'thing_1': ['usage_1_of_thing_1', 'usage_2_of_thing_1'],
            'thing_2': ['usage_1_of_thing_2', 'usage_2_of_thing_2'],
            'thing_3': ['usage_1_of_thing_3', 'usage_2_of_thing_3'],
        }
    }

    new_config = {
        'deprecated_things': [
            'thing_1',
            'thing_3'
        ],
        'usage': {
            'thing_1': ['usage_1_of_thing_1', 'usage_2_of_thing_1'],
            'thing_3': [],
            'thing_not_in_existing_config': ['usage']
        }
    }

    shitlist.test(
        existing_config=existing_config,
        new_config=new_config
    )


def test_find_usages(pytestconfig):
    test_root = PosixPath(pytestconfig.rootpath)

    deprecated_things = [
        'tests.example_module::wrapped_2',
        'tests.example_module::wrapped_1'
    ]

    result = shitlist.find_usages(str(test_root.parent), deprecated_things)

    expected_result = {
        'tests.example_module::wrapped_2': ['example_module.example_file::wrapped_3'],
        'tests.example_module::wrapped_1': ['example_module.example_file::wrapped_3']
    }
    assert_that(result, equal_to(expected_result))

