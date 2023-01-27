import shitlist


def not_wrapped():
    wrapped_2()
    return 0


@shitlist.deprecate(alternative='test')
def wrapped_1():
    return 1


@shitlist.deprecate(alternative='test')
def wrapped_2():
    return 1
