import shitlist


def not_wrapped():
    wrapped()
    return 0


@shitlist.deprecate
def wrapped():
    return 1
