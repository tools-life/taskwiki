from __future__ import print_function
import re
import os
import pickle
import sys
import vim  # pylint: disable=F0401

# Insert the taskwiki on the python path
BASE_DIR = vim.eval("s:plugin_path")
sys.path.insert(0, os.path.join(BASE_DIR, 'taskwiki'))

import errors
# Handle exceptions without traceback, if they're TaskWikiException
def output_exception(exception_type, value, tb):
    if exception_type is errors.TaskWikiException:
        print(unicode(value), file=sys.stderr)
    else:
        sys.__excepthook__(exception_type, value, tb)

sys.excepthook = output_exception

import cache
import sort
import util
import viewport

# Initialize the cache
cache = cache.TaskCache()

# Check the necessary dependencies first
util.enforce_dependencies(cache)

class WholeBuffer(object):
    @staticmethod
    def update_from_tw():
        """
        Updates all the incomplete tasks in the vimwiki file if the info from TW is different.
        """

        cache.reset()
        cache.load_tasks()
        cache.load_vwtasks(buffer_has_authority=False)
        cache.load_viewports()
        cache.update_vwtasks_from_tasks()
        cache.update_vwtasks_in_buffer()
        cache.evaluate_viewports()

    @staticmethod
    def update_to_tw():
        """
        Updates all tasks that differ from their TaskWarrior representation.
        """

        cache.reset()
        cache.load_tasks()
        cache.load_vwtasks()
        cache.load_viewports()
        cache.save_tasks()
        cache.update_vwtasks_in_buffer()
        cache.evaluate_viewports()


class SelectedTasks(object):
    def __init__(self):
        # Reset cache, otherwise old line content may be used
        cache.reset()

        # Find relevant TaskWarrior instance
        self.tw = cache.get_relevant_tw()

        # Load the current tasks
        range_tasks = [cache.vwtask[i] for i in util.selected_line_numbers()]
        self.tasks = [t for t in range_tasks if t is not None]

        if not self.tasks:
            print("No tasks selected.")

    def annotate(self, annotation):
        if not annotation:
            with util.current_line_highlighted():
                annotation = util.get_input("Enter annotation: ")

        for vimwikitask in self.tasks:
            vimwikitask.task.add_annotation(annotation)
            print("Task \"{0}\" annotated.".format(vimwikitask['description']))

    def done(self):
        # Multiple VimwikiTasks might refer to the same task, so make sure
        # we do not complete one task twice
        for task in set(vimwikitask.task for vimwikitask in self.tasks):
            task.done()

        # Update the lines in the buffer
        for vimwikitask in self.tasks:
            vimwikitask.update_from_task()
            vimwikitask.update_in_buffer()
            print("Task \"{0}\" completed.".format(vimwikitask['description']))

    def info(self):
        for vimwikitask in self.tasks:
            out = util.tw_execute_safely(self.tw, [vimwikitask.uuid, 'info'])
            if out:
                util.show_in_split(out, name='info', activate_cursorline=True)
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
            vim.command("TW rc:{0} rc.context: {1}"
                        .format(port.tw.taskrc_location, port.raw_filter))
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
            with util.current_line_highlighted():
                modstring = util.get_input("Enter modifications: ")

        # We might have two same tasks in the range, make sure we do not pass the
        # same uuid twice
        unique_tasks = set(vimwikitask.task['uuid'] for vimwikitask in self.tasks)
        uuids = list(unique_tasks)

        # Generate the arguments from the modstring
        args = util.tw_modstring_to_args(modstring)

        # Modify all tasks at once
        output = util.tw_execute_safely(self.tw, uuids + ['mod'] + args)

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

    def sort(self, sortstring):
        sort.TaskSorter(cache, self.tasks, sortstring).execute()


class Mappings(object):

    @staticmethod
    def task_info_or_vimwiki_follow_link():
        # If the line under cursor contains task, toggle info
        # otherwise do the default VimwikiFollowLink
        position = util.get_current_line_number()

        if cache.vwtask[position] is not None:
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
            "Ordering used: {3}\n"
            "Matching taskwarrior tasks: {4}\n"
            "Displayed tasks: {5}\n"
            "Tasks to be added: {6}\n"
            "Tasks to be deleted: {7}\n"
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
                port.sort,
                len(port.matching_tasks),
                len(port.tasks),
                ', '.join(map(unicode, to_add)),
                ', '.join(map(unicode, to_del)),
            )

            # Show in the split
            lines = template_formatted.splitlines()
            util.show_in_split(lines, activate_cursorline=True)

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

    def set_proper_colors(self):
        tw_color_counterparts = {
            'TaskWikiTaskActive': 'color.active',
            'TaskWikiTaskCompleted': 'color.completed',
            'TaskWikiTaskDeleted': 'color.deleted',
        }

        taskwiki_native_colors = {
            'TaskWikiTaskActive': 'Type',
            'TaskWikiTaskCompleted': 'Comment',
            'TaskWikiTaskDeleted': 'Error',
            'TaskWikiTaskPriority': 'Error',
        }

        # If tw support is enabled, try to find definition in TW first
        if vim.vars.get('taskwiki_source_tw_colors'):

            tw = cache.get_relevant_tw()

            for syntax in tw_color_counterparts.keys():
                tw_def = tw.config.get(tw_color_counterparts[syntax])

                if tw_def:
                    vim_def = util.convert_colorstring_for_vim(tw_def)
                    vim.command('hi def {0} {1}'.format(syntax, vim_def))

        # Define taskwiki (native) color. This can be overriden by user
        # by using :hi <group name> <color> command.
        for syntax in taskwiki_native_colors.keys():
            vim.command('hi def link {0} {1}'
                        .format(syntax, taskwiki_native_colors[syntax]))


class Split(object):
    command = None
    split_name = None
    colorful = False
    maxwidth = False
    maxheight = False
    vertical = False
    cursorline = True
    size = None
    tw_extra_args = []

    def __init__(self, args):
        self.args = self._process_args(args)
        self.split_name = self.split_name or self.command
        self.tw = cache.get_relevant_tw()

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

    @property
    def full_args(self):
        return self.args + [self.command] + self.tw_extra_args

    def execute(self):
        if self.colorful:
            output = util.tw_execute_colorful(self.tw, self.full_args,
                                              allow_failure=False,
                                              maxwidth=self.maxwidth,
                                              maxheight=self.maxheight)
        else:
            output = util.tw_execute_safely(self.tw, self.full_args)

        util.show_in_split(
            output,
            size=self.size,
            name=self.split_name,
            vertical=self.vertical,
            activate_cursorline=self.cursorline,
        )


class CallbackSplitMixin(object):

    split_cursorline = False

    def __init__(self, args):
        super(CallbackSplitMixin, self).__init__(args)
        self.selected = SelectedTasks()

    def execute(self):
        super(CallbackSplitMixin, self).execute()

        # Close the split if the user leaves it
        vim.command('au BufLeave <buffer> :bwipe')

        # SREMatch objecets cannot be pickled
        cache.line.clear()

        # We can't save the current instance in vim variable
        # so save the pickled version
        vim.current.buffer.vars['taskwiki_callback'] = pickle.dumps(self)

        # Remap <CR> to calling the callback and wiping the buffer
        vim.command(
            "nnoremap <silent> <buffer> <enter> :py "
            "callback = pickle.loads("
                "vim.current.buffer.vars['taskwiki_callback']); "
            "callback.callback(); "
            "vim.command('bwipe') <CR>"
        )

        # Show cursorline in split if required
        if self.split_cursorline:
            vim.current.window.options['cursorline'] = True

    def callback(self):
        raise NotImplementedError("No callback defined.")


class SplitProjects(Split):
    command = 'projects'
    vertical = True


class ChooseSplitProjects(CallbackSplitMixin, SplitProjects):
    split_cursorline = True

    def get_selected_project(self):
        project_re = re.compile(r'^(?P<indent>\s*)(?P<name>[^\s]+)\s+[0-9]+$')

        project_parts = []
        current_indent = None
        indented_less = lambda s: (current_indent is None or
                                   len(s) < current_indent)

        for line in util.get_lines_above():
            match = project_re.match(line)

            if match and indented_less(match.group('indent')):
                current_indent = len(match.group('indent'))
                project_parts.append(match.group('name'))

        # Properly handle selected (none)
        if project_parts == ['(none)']:
            project_parts = []

        project_parts.reverse()
        return '.'.join(project_parts)

    def callback(self):
        project = self.get_selected_project()
        self.selected.modify("project:{0}".format(project))


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

    # Task calendar does not take filter and in general uses
    # command-suffix syntax
    def __init__(self, args):
        self.args = []
        self.tw_extra_args = util.tw_modstring_to_args(args)
        self.split_name = self.split_name or self.command
        self.tw = cache.get_relevant_tw()


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


class ChooseSplitTags(CallbackSplitMixin, SplitTags):
    split_cursorline = True

    def get_selected_tag(self):
        tag_re = re.compile(r'^(?P<name>[^\s]+)\s+[0-9]+$')
        match = tag_re.match(vim.current.line)

        if match:
            return match.group('name')
        else:
            raise errors.TaskWikiException("No tag selected.")

    def callback(self):
        tag = self.get_selected_tag()
        self.selected.modify("+{0}".format(tag))


if __name__ == '__main__':
    WholeBuffer.update_from_tw()
    Meta().integrate_tagbar()
    Meta().set_proper_colors()
