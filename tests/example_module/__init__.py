import shitlist


def not_wrapped():
    wrapped_2()
    return 0


@shitlist.deprecate
def wrapped_1():
    return 1


@shitlist.deprecate
def wrapped_2():
    return 1
