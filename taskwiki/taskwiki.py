from __future__ import print_function
import os
import sys
import vim  # pylint: disable=F0401

from tasklib.task import TaskWarrior

# Insert the taskwiki on the python path
BASE_DIR = vim.eval("s:plugin_path")
sys.path.insert(0, os.path.join(BASE_DIR, 'taskwiki'))

# Handle exceptions without traceback, if they're TaskWikiException
def output_exception(exception_type, value, tb):
    if exception_type is util.TaskWikiException:
        print(unicode(value), file=sys.stderr)
    else:
        sys.__excepthook__(exception_type, value, tb)

sys.excepthook = output_exception

import cache
import util
import viewport

"""
How this plugin works:

    1.) On startup, it reads all the tasks and syncs info TW -> Vimwiki file. Task is identified by their
        uuid.
    2.) When saving, the opposite sync is performed (Vimwiki -> TW direction).
        a) if task is marked as subtask by indentation, the dependency is created between
"""

cache = cache.TaskCache()


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

    def annotate(self, annotation):
        if not annotation:
            annotation = util.get_input("Enter annotation: ")

        for vimwikitask in self.tasks:
            vimwikitask.task.add_annotation(annotation)
            print("Task \"{0}\" annotated.".format(vimwikitask['description']))

    def info(self):
        for vimwikitask in self.tasks:
            out = util.tw_execute_safely(self.tw, [vimwikitask.uuid, 'info'])
            if out:
                util.show_in_split(out, name='info')
            break  # Show only one task

    def edit(self):
        for vimwikitask in self.tasks:
            vim.command('! task {0} edit'.format(vimwikitask.uuid))

    def link(self):
        path = util.get_absolute_filepath()
        for vimwikitask in self.tasks:
            vimwikitask.task.add_annotation("wiki: {0}".format(path))
            print("Task \"{0}\" linked.".format(vimwikitask['description']))

    def grid(self):
        port = viewport.ViewPort.find_closest(cache)
        if port:
            vim.command("TW rc.context: {0}".format(port.raw_filter))
        else:
            print("No viewport detected.", file=sys.stderr)

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
        output = util.tw_execute_safely(self.tw, [uuids, 'mod'] + args)

        # Update the touched tasks in buffer, if needed
        cache.load_tasks()
        cache.update_vwtasks_from_tasks()
        cache.update_vwtasks_in_buffer()

        # Output the feedback from TW
        if output:
            print(output[-1])

    def start(self):
        # Multiple VimwikiTasks might refer to the same task, so make sure
        # we do not start one task twice
        for task in set(vimwikitask.task for vimwikitask in self.tasks):
            task.start()

        # Update the lines in the buffer
        for vimwikitask in self.tasks:
            vimwikitask.update_from_task()
            vimwikitask.update_in_buffer()
            print("Task \"{0}\" started.".format(vimwikitask['description']))


    def stop(self):
        # Multiple VimwikiTasks might refer to the same task, so make sure
        # we do not stop one task twice
        for task in set(vimwikitask.task for vimwikitask in self.tasks):
            task.stop()

        # Update the lines in the buffer
        for vimwikitask in self.tasks:
            vimwikitask.update_from_task()
            vimwikitask.update_in_buffer()
            print("Task \"{0}\" stopped.".format(vimwikitask['description']))


class Mappings(object):

    @staticmethod
    def task_info_or_vimwiki_follow_link():
        # If the line under cursor contains task, toggle info
        # otherwise do the default VimwikiFollowLink
        position = util.get_current_line_number()

        if cache[position] is not None:
            SelectedTasks().info()
        else:
            port = viewport.ViewPort.from_line(position, cache)
            if port is not None:
                Meta().inspect_viewport()
            else:
                vim.command('VimwikiFollowLink')


class Meta(object):

    def inspect_viewport(self):
        position = util.get_current_line_number()
        port = viewport.ViewPort.from_line(position, cache)

        if port.meta.get('visible') is False:
            cache.reset()
            cache.load_vwtasks()
            cache.load_tasks()

        template = (
            "ViewPort inspection:\n"
            "--------------------\n"
            "Name: {0}\n"
            "Filter used: {1}\n"
            "Defaults used: {2}\n"
            "Matching taskwarrior tasks: {3}\n"
            "Displayed tasks: {4}\n"
            "Tasks to be added: {5}\n"
            "Tasks to be deleted: {6}\n"
        )

        if port is not None:
            # Load the tasks under the viewport
            port.load_tasks()

            to_add, to_del = port.get_tasks_to_add_and_del()

            # Fill in the interesting info in the template
            template_formatted = template.format(
                port.name,
                port.raw_filter,
                port.raw_defaults,
                len(port.matching_tasks),
                len(port.tasks),
                ', '.join(map(unicode, to_add)),
                ', '.join(map(unicode, to_del)),
            )

            # Show in the split
            lines = template_formatted.splitlines()
            util.show_in_split(lines)

    def integrate_tagbar(self):
        tagbar_available = vim.eval('exists(":Tagbar")') == '2'
        if tagbar_available:
            vim.vars['tagbar_type_vimwiki'] = {
                'ctagstype': 'default',
                'kinds': ['h:header', 'i:inside', 'v:viewport'],
                'sro': '&&&',
                'kind2scope': {'h':'header', 'v':'viewport'},
                'sort': 0,
                'ctagsbin': os.path.join(BASE_DIR, 'extra/vwtags.py'),
                'ctagsargs': 'default'
                }


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
        # If no argument has been passed, locate the closest viewport,
        # if any exists, and use its filter.
        else:
            port = viewport.ViewPort.find_closest(cache)
            return port.taskfilter if port is not None else []

    def execute(self):
        args = self.args + [self.command] + self.tw_extra_args
        if self.colorful:
            output = util.tw_execute_colorful(tw, args,
                                              allow_failure=False,
                                              maxwidth=self.maxwidth,
                                              maxheight=self.maxheight)
        else:
            output = util.tw_execute_safely(tw, args)

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


class SplitGhistoryMonthly(Split):
    command = 'ghistory.monthly'
    colorful = True
    maxwidth = True


class SplitGhistoryAnnual(Split):
    command = 'ghistory.annual'
    colorful = True
    maxwidth = True


class SplitHistoryMonthly(Split):
    command = 'history.monthly'
    colorful = True
    vertical = True


class SplitHistoryAnnual(Split):
    command = 'history.annual'
    colorful = True
    vertical = True


class SplitStats(Split):
    command = 'stats'
    colorful = True
    vertical = True


class SplitTags(Split):
    command = 'tags'
    colorful = True
    vertical = True


if __name__ == '__main__':
    WholeBuffer.update_from_tw()
    Meta().integrate_tagbar()
