"""
Contains TaskWiki-specific exceptions.
"""

from __future__ import print_function
import six
import sys


class VimPrettyException(Exception):
    pass


class TaskWikiException(VimPrettyException):
    """Used to interrupt a TaskWiki command/event and notify the user."""
    pass


def pretty_exception_handler(original_function):
    """
    Wraps a given function object to catch and process all the
    VimPrettyExceptions encountered.
    """
    def wrapped_function(*args, **kwargs):
        try:
            original_function(*args, **kwargs)
        except VimPrettyException as e:
            print(six.text_type(e), file=sys.stderr)

    return wrapped_function
