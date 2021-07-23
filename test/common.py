import inspect


def _grandparent_name():
    return inspect.currentframe().f_back.f_back.f_code.co_name


def log_enter():
    print("{} enter".format(_grandparent_name()))


def log_exit():
    print("{} exit".format(_grandparent_name()))
