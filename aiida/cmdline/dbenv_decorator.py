from click_spinner import spinner as cli_spinner


def load_dbenv_if_not_loaded(**kwargs):
    """
    load dbenv if necessary, run spinner meanwhile to show command hasn't crashed
    """
    with cli_spinner():
        from aiida.backends.utils import load_dbenv, is_dbenv_loaded
        if not is_dbenv_loaded():
            load_dbenv(**kwargs)


def aiida_dbenv(function):
    """
    a function decorator that loads the dbenv if necessary before running the function
    """
    def decorated_function(*args, **kwargs):
        """load dbenv if not yet loaded, then run the original function"""
        load_dbenv_if_not_loaded()
        return function(*args, **kwargs)
    return decorated_function