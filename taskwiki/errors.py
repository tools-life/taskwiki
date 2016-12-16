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


# Handle error without traceback, if they're descendants of VimPrettyException
def output_exception(exception_type, value, traceback):
    if any(['VimPretty' in t.__name__ for t in exception_type.mro()]):
        print(six.text_type(value), file=sys.stderr)
    else:
        sys.__excepthook__(exception_type, value, traceback)

# Wrap the original except hook
sys.excepthook = output_exception
