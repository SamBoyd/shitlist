import shitlist
from tests.example_module import wrapped_2
from tests import example_module


@shitlist.deprecate(alternative='test')
def wrapped_3():
    wrapped_2()
    example_module.wrapped_1()
    return 1
