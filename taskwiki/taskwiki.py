import sys
import vim  # pylint: disable=F0401

from tasklib.task import TaskWarrior, Task

# Insert the taskwiki on the python path
sys.path.insert(0, vim.eval("s:plugin_path") + '/taskwiki')

import cache
import util
import vwtask
import viewport

"""
How this plugin works:

    1.) On startup, it reads all the tasks and syncs info TW -> Vimwiki file. Task is identified by their
        uuid.
    2.) When saving, the opposite sync is performed (Vimwiki -> TW direction).
        a) if task is marked as subtask by indentation, the dependency is created between
"""


tw = TaskWarrior()
cache = cache.TaskCache(tw)

# Make sure context is not respected
tw.config.update({'context':''})


class WholeBuffer(object):
    @staticmethod
    def update_from_tw():
        """
        Updates all the incomplete tasks in the vimwiki file if the info from TW is different.
        """

        cache.load_vwtasks()
        cache.load_tasks()
        cache.update_vwtasks_from_tasks()
        cache.update_vwtasks_in_buffer()
        cache.evaluate_viewports()

    @staticmethod
    def update_to_tw():
        """
        Updates all tasks that differ from their TaskWarrior representation.
        """

        cache.reset()
        cache.load_vwtasks()
        cache.load_tasks()
        cache.save_tasks()
        cache.update_vwtasks_in_buffer()
        cache.evaluate_viewports()


class SelectedTasks(object):
    def __init__(self):
        self.tw = tw

        # Reset cache, otherwise old line content may be used
        cache.reset()

        # Load the current tasks
        range_tasks = [cache[i] for i in util.selected_line_numbers()]
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

    def delete(self):
        # Delete the tasks in TaskWarrior
        # Multiple VimwikiTasks might refer to the same task, so make sure
        # we do not delete one task twice
        for task in set(vimwikitask.task for vimwikitask in self.tasks):
            task.delete()

        # Remove the lines in the buffer
        for vimwikitask in self.tasks:
            cache.remove_line(vimwikitask['line_number'])
            print("Task \"{0}\" deleted.".format(vimwikitask['description']))

    def modify(self, modstring):
        # If no modstring was passed as argument, ask the user interactively
        if not modstring:
            modstring = util.get_input("Enter modifications: ")

        # We might have two same tasks in the range, make sure we do not pass the
        # same uuid twice
        unique_tasks = set(vimwikitask.task['uuid'] for vimwikitask in self.tasks)
        uuids = ','.join(unique_tasks)

        # Generate the arguments from the modstring
        args = util.tw_modstring_to_args(modstring)

        # Modify all tasks at once
        output = self.tw.execute_command([uuids, 'mod'] + args)

        # Update the touched tasks in buffer, if needed
        cache.load_tasks()
        cache.update_vwtasks_from_tasks()
        cache.update_vwtasks_in_buffer()

        # Output the feedback from TW
        if output:
            print(output[-1])


class Mappings(object):

    @staticmethod
    def task_info_or_vimwiki_follow_link():
        # If the line under cursor contains task, toggle info
        # otherwise do the default VimwikiFollowLink
        if cache[util.get_current_line_number()] is not None:
            SelectedTasks().info()
        else:
            vim.command('VimwikiFollowLink')


class Split(object):
    command = None
    split_name = None
    colorful = False
    maxwidth = False
    maxheight = False
    vertical = False
    tw_extra_args = []

    def __init__(self, args):
        self.args = self._process_args(args)
        self.split_name = self.split_name or self.command

    def _process_args(self, args):
        tw_args = util.tw_modstring_to_args(args)

        # If only 'global' argument has been passed, then no
        # filter should be applied
        if tw_args == ['global']:
            return []
        # If unempty filter has been passed, then use that
        elif tw_args != []:
            return tw_args
        # If no argument has been passed, locate the closest viewport
        # and use its filter
        else:
            return viewport.ViewPort.find_closest(cache).taskfilter or []

    def execute(self):
        args = self.args + [self.command] + self.tw_extra_args
        if self.colorful:
            output = util.tw_execute_colorful(tw, args,
                                              maxwidth=self.maxwidth,
                                              maxheight=self.maxheight)
        else:
            output = tw.execute_command(args)

        util.show_in_split(
            output,
            name=self.split_name,
            vertical=self.vertical,
        )


class SplitProjects(Split):
    command = 'projects'
    vertical = True


class SplitSummary(Split):
    command = 'summary'
    vertical = True
    colorful = True


class SplitBurndownDaily(Split):
    command = 'burndown.daily'
    colorful = True
    maxwidth = True


class SplitBurndownWeekly(Split):
    command = 'burndown.weekly'
    colorful = True
    maxwidth = True


class SplitBurndownMonthly(Split):
    command = 'burndown.monthly'
    colorful = True
    maxwidth = True


class SplitCalendar(Split):
    command = 'calendar'
    colorful = True
    maxwidth = True

    # Task calendar does not take fitler and in general uses
    # command-suffix syntax
    def __init__(self, args):
        self.args = []
        self.tw_extra_args = util.tw_modstring_to_args(args)
        self.split_name = self.split_name or self.command


if __name__ == '__main__':
    WholeBuffer.update_from_tw()
