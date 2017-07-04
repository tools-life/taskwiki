from __future__ import print_function
import base64
import re
import os
import pickle
import six
import sys
import vim  # pylint: disable=F0401

# Insert the taskwiki on the python path
BASE_DIR = vim.eval("s:plugin_path")
sys.path.insert(0, BASE_DIR)

from taskwiki import errors
from taskwiki import cache as cache_module
from taskwiki import sort
from taskwiki import util
from taskwiki import viewport
from taskwiki import decorators


cache = cache_module.CacheRegistry()
cache.load_current()


class WholeBuffer(object):
    @staticmethod
    @errors.pretty_exception_handler
    @decorators.hold_vim_cursor
    def update_from_tw():
        """
        Updates all the incomplete tasks in the vimwiki file if the info from TW is different.
        """

        c = cache()
        c.reset()
        c.load_syntax()
        c.load_tasks()
        c.load_vwtasks(buffer_has_authority=False)
        c.load_viewports()
        c.update_vwtasks_from_tasks()
        c.update_vwtasks_in_buffer()
        c.evaluate_viewports()
        c.buffer.push()

    @staticmethod
    @errors.pretty_exception_handler
    @decorators.hold_vim_cursor
    def update_to_tw():
        """
        Updates all tasks that differ from their TaskWarrior representation.
        """

        c = cache()
        c.reset()
        c.load_syntax()
        c.load_tasks()
        c.load_vwtasks()
        c.load_viewports()
        c.save_tasks()
        c.update_vwtasks_in_buffer()
        c.evaluate_viewports()
        c.buffer.push()


class SelectedTasks(object):

    # Keeps track of the last action performed on any selected tasks
    last_action = {}

    @errors.pretty_exception_handler
    def __init__(self):
        # Reset cache(), otherwise old line content may be used
        cache().reset()

        # Find relevant TaskWarrior instance
        self.tw = cache().get_relevant_tw()

        # Load the current tasks
        range_tasks = [cache().vwtask[i] for i in util.selected_line_numbers()]
        self.tasks = [t for t in range_tasks if t is not None]

        if not self.tasks:
            print("No tasks selected.")

    @classmethod
    def save_action(cls, method, *args):
        cls.last_action = {'method': method, 'args': args}

    @errors.pretty_exception_handler
    def annotate(self, annotation):
        if not annotation:
            with util.current_line_highlighted():
                annotation = util.get_input("Enter annotation: ")

        for vimwikitask in self.tasks:
            vimwikitask.task.add_annotation(annotation)
            print(u"Task \"{0}\" annotated.".format(vimwikitask['description']))

        self.save_action('annotate', annotation)

    @errors.pretty_exception_handler
    def done(self):
        # Multiple VimwikiTasks might refer to the same task, so make sure
        # we do not complete one task twice
        for task in set(vimwikitask.task for vimwikitask in self.tasks):
            task.done()

        # Update the lines in the buffer
        for vimwikitask in self.tasks:
            vimwikitask.update_from_task()
            vimwikitask.update_in_buffer()
            print(u"Task \"{0}\" completed.".format(vimwikitask['description']))

        cache().buffer.push()
        self.save_action('done')

    @errors.pretty_exception_handler
    def info(self):
        for vimwikitask in self.tasks:
            out = util.tw_execute_safely(self.tw, [vimwikitask.uuid, 'info'])
            if out:
                util.show_in_split(out, name='info', activate_cursorline=True)
            break  # Show only one task

    @errors.pretty_exception_handler
    def edit(self):
        for vimwikitask in self.tasks:
            alternate_data_location = self.tw.overrides.get('data.location')
            location_override = ('rc.data.location=' + alternate_data_location
                                 if alternate_data_location else '')

            # Build command template, it is different for neovim and vim
            command = (
                ('terminal' if util.NEOVIM else '!') +
                ' task {0} {1} edit'
            )
            vim.command(command.format(location_override, vimwikitask.uuid))

        self.save_action('edit')

    @errors.pretty_exception_handler
    def link(self):
        path = util.get_absolute_filepath()
        for vimwikitask in self.tasks:
            vimwikitask.task.add_annotation(u"wiki: {0}".format(path))
            print(u"Task \"{0}\" linked.".format(vimwikitask['description']))
        self.save_action('link')

    @errors.pretty_exception_handler
    def grid(self):
        port = viewport.ViewPort.find_closest(cache())
        if port:
            vim.command("TW rc:{0} rc.context: {1}"
                        .format(port.tw.taskrc_location, port.raw_filter))
        else:
            print("No viewport detected.", file=sys.stderr)

    @errors.pretty_exception_handler
    def delete(self):
        # Delete the tasks in TaskWarrior
        # Multiple VimwikiTasks might refer to the same task, so make sure
        # we do not delete one task twice
        for task in set(vimwikitask.task for vimwikitask in self.tasks):
            task.delete()

        # Remove the lines in the buffer
        for vimwikitask in self.tasks:
            cache().remove_line(vimwikitask['line_number'])
            print(u"Task \"{0}\" deleted.".format(vimwikitask['description']))

        cache().buffer.push()
        self.save_action('delete')

    @errors.pretty_exception_handler
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
        cache().load_tasks()
        cache().update_vwtasks_from_tasks()
        cache().update_vwtasks_in_buffer()

        # Output the feedback from TW
        if output:
            print(output[-1])

        cache().buffer.push()
        self.save_action('modify', modstring)

    def redo(self):
        """
        Performs the last modification applied to any selected tasks once again.
        """

        if self.__class__.last_action:
            method = getattr(self, self.__class__.last_action['method'])
            method(*self.__class__.last_action.get('args', tuple()))


    @errors.pretty_exception_handler
    def start(self):
        # Multiple VimwikiTasks might refer to the same task, so make sure
        # we do not start one task twice
        for task in set(vimwikitask.task for vimwikitask in self.tasks):
            task.start()

        # Update the lines in the buffer
        for vimwikitask in self.tasks:
            vimwikitask.update_from_task()
            vimwikitask.update_in_buffer()
            print(u"Task \"{0}\" started.".format(vimwikitask['description']))

        cache().buffer.push()
        self.save_action('start')

    @errors.pretty_exception_handler
    def stop(self):
        # Multiple VimwikiTasks might refer to the same task, so make sure
        # we do not stop one task twice
        for task in set(vimwikitask.task for vimwikitask in self.tasks):
            task.stop()

        # Update the lines in the buffer
        for vimwikitask in self.tasks:
            vimwikitask.update_from_task()
            vimwikitask.update_in_buffer()
            print(u"Task \"{0}\" stopped.".format(vimwikitask['description']))

        cache().buffer.push()
        self.save_action('stop')

    @errors.pretty_exception_handler
    def sort(self, sortstring):
        sort.TaskSorter(cache(), self.tasks, sortstring).execute()
        cache().buffer.push()


class Mappings(object):

    @staticmethod
    @errors.pretty_exception_handler
    def task_info_or_vimwiki_follow_link():
        # Reset the cache() to use up-to-date buffer content
        cache().reset()

        # If the line under cursor contains task, toggle info
        # otherwise do the default VimwikiFollowLink
        row = util.get_current_line_number()
        column = util.get_current_column_number()
        line = cache().buffer[row]

        # Detect if the cursor stands on a vimwiki link,
        # if so, trigger it
        inside_vimwiki_link = all([
            '[[' in line,
            ']]' in line,
            column >= line.find('[['),
            column <= line.find(']]') + 1
        ])

        if inside_vimwiki_link:
            vim.command('VimwikiFollowLink')
            return

        # No link detected, check for viewport or a task
        if cache().vwtask[row] is not None:
            SelectedTasks().info()
            return
        else:
            port = viewport.ViewPort.from_line(row, cache())
            if port is not None:
                Meta().inspect_viewport()
                return

        # No link detected, not a viewport or a task, so delegate to
        # VimwikiFollowLink for link creation
        vim.command('VimwikiFollowLink')



class Meta(object):

    @errors.pretty_exception_handler
    def inspect_viewport(self):
        position = util.get_current_line_number()
        port = viewport.ViewPort.from_line(position, cache())

        if port.meta.get('visible') is False:
            cache().reset()
            cache().load_vwtasks()
            cache().load_tasks()

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
                port.name if six.PY3 else port.name.encode('utf-8'),
                port.raw_filter if six.PY3 else port.raw_filter.encode('utf-8'),
                port.raw_defaults if six.PY3 else port.raw_defaults.encode('utf-8'),
                port.sort,
                len(port.matching_tasks),
                len(port.tasks),
                ', '.join(map(six.text_type, to_add)),
                ', '.join(map(six.text_type, to_del)),
            )

            # Show in the split
            lines = template_formatted.splitlines()
            util.show_in_split(lines, activate_cursorline=True)

    @errors.pretty_exception_handler
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

    @errors.pretty_exception_handler
    def set_proper_colors(self):
        tw_color_counterparts = {
            'TaskWikiTaskActive': 'color.active',
            'TaskWikiTaskCompleted': 'color.completed',
            'TaskWikiTaskDeleted': 'color.deleted',
            'TaskWikiTaskRecurring': 'color.recurring',
            'TaskWikiTaskWaiting': 'color.completed',
        }

        taskwiki_native_colors = {
            'TaskWikiTaskActive': 'Type',
            'TaskWikiTaskCompleted': 'Comment',
            'TaskWikiTaskRecurring': 'Comment',
            'TaskWikiTaskWaiting': 'Comment',
            'TaskWikiTaskDeleted': 'Error',
            'TaskWikiTaskPriority': 'Error',
        }

        # If tw support is enabled, try to find definition in TW first
        if util.get_var('taskwiki_source_tw_colors'):

            tw = cache().get_relevant_tw()

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

    @errors.pretty_exception_handler
    def __init__(self, args):
        self.args = self._process_args(args)
        self.split_name = self.split_name or self.command
        self.tw = cache().get_relevant_tw()

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
            port = viewport.ViewPort.find_closest(cache())
            return port.taskfilter if port is not None else []

    @property
    def full_args(self):
        return self.args + [self.command] + self.tw_extra_args

    @errors.pretty_exception_handler
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

    @errors.pretty_exception_handler
    def __init__(self, args):
        super(CallbackSplitMixin, self).__init__(args)
        self.selected = SelectedTasks()

    @errors.pretty_exception_handler
    def execute(self):
        super(CallbackSplitMixin, self).execute()

        # Close the split if the user leaves it
        vim.command('au BufLeave <buffer> :bwipe')

        # SREMatch objecets cannot be pickled
        cache().line.clear()

        # We can't save the current instance in vim variable
        # so save the pickled version
        dump = pickle.dumps((
            {k:v for k,v in self.__dict__.items() if k != 'selected'},
            self.selected.__dict__)
        )

        vim.current.buffer.vars['taskwiki_callback'] = base64.encodestring(
            bytes(dump)
        )

        # Remap <CR> to calling the callback and wiping the buffer
        vim.command(
            "nnoremap <silent> <buffer> <enter> :"
            + util.get_var('taskwiki_py') +
            "callback = {0}('');".format(self.__class__.__name__) +
            "orig_dict, selected_dict = pickle.loads("
            "base64.decodestring("
              "six.b(util.get_var('taskwiki_callback', "
                                  "vars_obj=vim.current.buffer.vars)))); "
            "callback.__dict__.update(orig_dict);"
            "callback.selected.__dict__ = selected_dict;"
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

    def _get_selected_project(self):
        project_re = re.compile(r'^(?P<indent>\s*)(?P<name>[^\s]+)\s+[0-9]+$',
                                re.UNICODE)

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
        if six.PY2:
            return u'.'.join([p.decode('utf-8') for p in project_parts])
        else:
            return u'.'.join(project_parts)

    @errors.pretty_exception_handler
    def callback(self):
        project = self._get_selected_project()
        self.selected.modify(u"project:{0}".format(project))


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
    @errors.pretty_exception_handler
    def __init__(self, args):
        self.args = []
        self.tw_extra_args = util.tw_modstring_to_args(args)
        self.split_name = self.split_name or self.command
        self.tw = cache().get_relevant_tw()


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

    def _get_selected_tag(self):
        tag_re = re.compile(r'^(?P<name>[^\s]+)\s+[0-9]+$', re.UNICODE)
        match = tag_re.match(vim.current.line)

        if match:
            tag = match.group('name')
            tag = tag.decode('utf-8') if six.PY2 else tag
            return tag
        else:
            raise errors.TaskWikiException("No tag selected.")

    @errors.pretty_exception_handler
    def callback(self):
        tag = self._get_selected_tag()
        self.selected.modify(u"+{0}".format(tag))


if __name__ == '__main__':
    WholeBuffer.update_from_tw()
    Meta().integrate_tagbar()
    Meta().set_proper_colors()
