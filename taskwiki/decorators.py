import vim  # pylint: disable=F0401

def hold_vim_cursor(original_function):
    """
    Decorator that wrap around to save cursor position and restore it
    """

    def wrapped_function(*args, **kwargs):
        vim.command('let save_pos = getpos(".")')
        original_function(*args, **kwargs)
        vim.command('call setpos(".", save_pos)')
    return wrapped_function
