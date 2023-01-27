import shitlist


def not_wrapped():
    wrapped()
    return 0


@shitlist.deprecate(alternative='test')
def wrapped():
    return 1
