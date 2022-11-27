from pathlib import PosixPath

import pytest
from hamcrest import assert_that, has_items, equal_to

import shitlist
from shitlist import deprecate, Config


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
    existing_config = Config(
        deprecated_things=[
            'thing_1',
            'thing_2',
            'thing_3'
        ],
        usage={
            'thing_1': ['usage_1_of_thing_1', 'usage_2_of_thing_1'],
            'thing_2': ['usage_1_of_thing_2', 'usage_2_of_thing_2'],
            'thing_3': ['usage_1_of_thing_3', 'usage_2_of_thing_3'],
        }
    )

    new_config = Config(
        deprecated_things=[
            'thing_1',
            'thing_2',
            'thing_3'
        ],
        usage={
            'thing_1': ['usage_1_of_thing_1', 'usage_2_of_thing_1'],
            'thing_2': ['usage_1_of_thing_2', 'usage_2_of_thing_2'],
            'thing_3': ['usage_1_of_thing_3', 'usage_2_of_thing_3', 'usage_3_of_thing_3'],
        }
    )

    with pytest.raises(shitlist.DeprecatedException):
        shitlist.test(
            existing_config=existing_config,
            new_config=new_config
        )


def test_shitlist_test_should_fail_if_reintroduce_a_previously_deprecated_thing():
    assert_that(True, equal_to(False))


def test_shitlist_test_passes():
    existing_config = Config(
        deprecated_things=[
            'thing_1',
            'thing_2',
            'thing_3'
        ],
        usage={
            'thing_1': ['usage_1_of_thing_1', 'usage_2_of_thing_1'],
            'thing_2': ['usage_1_of_thing_2', 'usage_2_of_thing_2'],
            'thing_3': ['usage_1_of_thing_3', 'usage_2_of_thing_3'],
        }
    )

    new_config = Config(
        deprecated_things=[
            'thing_1',
            'thing_3'
        ],
        usage={
            'thing_1': ['usage_1_of_thing_1', 'usage_2_of_thing_1'],
            'thing_3': [],
            'thing_not_in_existing_config': ['usage']
        }
    )

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


def test_update_config():
    existing_config = Config(
        deprecated_things=[
            'thing_1',
            'thing_2',
            'thing_3'
        ],
        usage={
            'thing_1': ['usage_1_of_thing_1', 'usage_2_of_thing_1'],
            'thing_2': ['usage_1_of_thing_2', 'usage_2_of_thing_2'],
            'thing_3': ['usage_1_of_thing_3', 'usage_2_of_thing_3'],
        }
    )

    new_config = Config(
        deprecated_things=[
            'thing_1',
            'thing_3',
            'thing_not_in_existing_config'
        ],
        usage={
            'thing_1': ['usage_1_of_thing_1', 'usage_2_of_thing_1'],
            'thing_3': ['usage_2_of_thing_3'],
            'thing_not_in_existing_config': ['usage']
        }
    )

    updated_config = shitlist.update(
        existing_config=existing_config,
        new_config=new_config
    )

    expected_config = Config(
        deprecated_things=[
            'thing_1',
            'thing_3',
            'thing_not_in_existing_config'
        ],
        usage={
            'thing_1': ['usage_1_of_thing_1', 'usage_2_of_thing_1'],
            'thing_3': ['usage_2_of_thing_3'],
            'thing_not_in_existing_config': ['usage']
        },
        removed_usages={
            'thing_3': ['usage_1_of_thing_3']
        },
        successfully_removed_things=[
            'thing_2',
        ]
    )

    assert_config_are_equal(updated_config, expected_config)


def test_ignores_directories(pytestconfig):
    test_root = PosixPath(pytestconfig.rootpath).parent

    walker = shitlist.TreeWalker(
        root_dir=test_root / 'example_module',
        ignore_directories=['submodule']
    )

    assert_that(walker.has_next, equal_to(True))

    assert_that(walker.next_file().name, equal_to('example_file.py'))
    assert_that(walker.next_file().name, equal_to('__init__.py'))

    assert_that(walker.has_next, equal_to(False))

def assert_config_are_equal(config_1: Config, config_2: Config):
    assert_that(
        config_1.deprecated_things,
        equal_to(config_2.deprecated_things),
        'property deprecated_things are not equal'
    )

    assert_that(
        config_1.usage,
        equal_to(config_2.usage),
        'property usage are not equal'
    )

    assert_that(
        config_1.removed_usages,
        equal_to(config_2.removed_usages),
        'property removed_usages are not equal'
    )

    assert_that(
        config_1.successfully_removed_things,
        equal_to(config_2.successfully_removed_things),
        'property successfully_removed_things are not equal'
    )
