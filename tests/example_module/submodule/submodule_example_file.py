from shitlist import deprecate


@deprecate(
    alternative='test'
)
def wrapped():
    return 1
