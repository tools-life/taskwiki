import copy
import pytz
import re
import vim

from datetime import datetime
from tasklib.task import TaskWarrior, Task

vim.command("echom '%s'" % vim.eval("s:plugin_path"))
# update the sys path to include the jedi_vim script
sys.path.insert(0, vim.eval("s:plugin_path") + "/taskwiki")

from regexp import *
from task import VimwikiTask

"""
How this plugin works:

    1.) On startup, it reads all the tasks and syncs info TW -> Vimwiki file. Task is identified by their
        uuid.
    2.) When saving, the opposite sync is performed (Vimwiki -> TW direction).
        a) if task is marked as subtask by indentation, the dependency is created between
"""


tw = TaskWarrior()
local_timezone = pytz.timezone('Europe/Bratislava')

cache = TaskCache(tw)


def update_from_tw():
    """
    Updates all the incomplete tasks in the vimwiki file if the info from TW is different.
    """

    for i in range(len(vim.current.buffer)):
        line = vim.current.buffer[i]

        if re.search(GENERIC_TASK, line):
            task = cache[i]
            task.update_from_tw()
            task.update_in_buffer()


def update_to_tw():
    """
    Updates all tasks that differ from their TaskWarrior representation.
    """

    cache.reset()

    for i in range(len(vim.current.buffer)):
        line = vim.current.buffer[i]

        # First load all the tasks to the cache (this will set dependency sets)
        if re.search(GENERIC_TASK, line):
            task = cache[i]

    for task in cache:
        task.save_to_tw()
        task.update_in_buffer()


class ViewPort(object):
    """
    Represents viewport with a given filter.
    """

if __name__ == '__main__':
    update_from_tw()

