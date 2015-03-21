import sys
import vim  # pylint: disable=F0401

from tasklib.task import TaskWarrior, Task

# Insert the taskwiki on the python path
sys.path.insert(0, vim.eval("s:plugin_path") + '/taskwiki')

import cache
import util
import vwtask

"""
How this plugin works:

    1.) On startup, it reads all the tasks and syncs info TW -> Vimwiki file. Task is identified by their
        uuid.
    2.) When saving, the opposite sync is performed (Vimwiki -> TW direction).
        a) if task is marked as subtask by indentation, the dependency is created between
"""


tw = TaskWarrior()
cache = cache.TaskCache(tw)


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

class SelectedTasks(object):
    def __init__(self):
        self.tw = tw

        # Reset cache, otherwise old line content may be used
        cache.reset()

        # Load the current tasks
        range_tasks = [vwtask.VimwikiTask.from_line(cache, i)
                       for i in util.selected_line_numbers()]
        self.tasks = [t for t in range_tasks if t is not None]

        if not self.tasks:
            print("No tasks selected.")

    def info(self):
        for vimwikitask in self.tasks:
            info = self.tw.execute_command([vimwikitask['uuid'], 'info'])
            util.show_in_split(info)
            break  # Show only one task

    def link(self):
        path = util.get_absolute_filepath()
        for vimwikitask in self.tasks:
            vimwikitask.task.add_annotation("wiki: {0}".format(path))
            print("Task \"{0}\" linked.".format(vimwikitask['description']))

if __name__ == '__main__':
    update_from_tw()
