import sys
import re
import vim

from tasklib.task import TaskWarrior, Task

# Insert the taskwiki on the python path
sys.path.insert(0, vim.eval("s:plugin_path") + '/taskwiki')

from regexp import *
from task import VimwikiTask
from cache import TaskCache

"""
How this plugin works:

    1.) On startup, it reads all the tasks and syncs info TW -> Vimwiki file. Task is identified by their
        uuid.
    2.) When saving, the opposite sync is performed (Vimwiki -> TW direction).
        a) if task is marked as subtask by indentation, the dependency is created between
"""


tw = TaskWarrior()
cache = TaskCache(tw)


def update_from_tw():
    """
    Updates all the incomplete tasks in the vimwiki file if the info from TW is different.
    """

    cache.load_buffer()
    cache.update_tasks()
    cache.update_buffer()
    cache.evaluate_viewports()


def update_to_tw():
    """
    Updates all tasks that differ from their TaskWarrior representation.
    """

    cache.reset()
    cache.load_buffer()
    cache.update_tasks()
    cache.save_tasks()
    cache.update_buffer()
    cache.evaluate_viewports()


if __name__ == '__main__':
    update_from_tw()
