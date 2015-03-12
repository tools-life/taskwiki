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

"""
How this plugin works:

    1.) On startup, it reads all the tasks and syncs info TW -> Vimwiki file. Task is identified by their
        uuid.
    2.) When saving, the opposite sync is performed (Vimwiki -> TW direction).
        a) if task is marked as subtask by indentation, the dependency is created between
"""


tw = TaskWarrior()
local_timezone = pytz.timezone('Europe/Bratislava')

class TaskCache(object):
    """
    A cache that holds all the tasks in the given file and prevents
    multiple redundant taskwarrior calls.
    """

    def __init__(self):
        self.cache = dict()

    def __getitem__(self, key):
        task = self.cache.get(key)

        if task is None:
            task = VimwikiTask(vim.current.buffer[key], key)
            self.cache[key] = task

        return task

    def __iter__(self):
#        iterated_cache = {
        while self.cache.keys():
            for key in list(self.cache.keys()):
                task = self.cache[key]
                if all([t.line_number not in self.cache.keys()
                        for t in task.add_dependencies]):
                    del self.cache[key]
                    yield task

    def reset(self):
        self.cache = dict()

#    def update_tasks(self):
#        tasks = [t

cache = TaskCache()


def convert_priority_from_tw_format(priority):
    return {None: 0, 'L': 1, 'M': 2, 'H': 3}[priority]


def convert_priority_to_tw_format(priority):
    return {0: None, 1: 'L', 2: 'M', 3: 'H'}[priority]


class VimwikiTask(object):
    def __init__(self, line, position):
        """
        Constructs a Vimwiki task from line at given position at the buffer
        """

        match = re.search(GENERIC_TASK, line)
        self.indent = match.group('space')
        self.text = match.group('text')
        self.uuid = match.group('uuid')  # can be None for new tasks
        self.due = match.group('due')  # TODO: convert to proper timestamp
        self.completed_mark = match.group('completed')
        self.completed = self.completed_mark is 'X'
        self.line_number = position
        self.priority = len(match.group('priority') or []) # This is either 0,1,2 or 3

        # We need to track depedency set in a extra attribute, since
        # this may be a new task, and hence it need not to be saved yet.
        # We circumvent this problem by iteration order in the TaskCache
        self.add_dependencies = set()

        # First set the task attribute to None, then try to load it, if possible
        self.task = None

        if self.uuid:
            try:
                self.task = tw.tasks.get(uuid=self.uuid)
            except Task.DoesNotExist:
                self.task = Task(tw)
                # If task cannot be loaded, we need to remove the UUID
                vim.command('echom "UUID not found: %s,'
                            'will be replaced if saved"' % self.uuid)
                self.uuid = None
        else:
            self.task = Task(tw)

        # To get local time aware timestamp, we need to convert to from local datetime
        # to UTC time, since that is what tasklib (correctly) uses
        if self.due:
            # With strptime, we get a native datetime object
            try:
                due_native_datetime = datetime.strptime(self.due, DATETIME_FORMAT)
            except ValueError:
                try:
                    due_native_datetime = datetime.strptime(self.due, DATE_FORMAT)
                except ValueError:
                    vim.command('echom "Taskwiki: Invalid timestamp on line %s, '
                                'ignored."' % self.line_number)

            # We need to interpret it as timezone aware object in user's timezone
            # This properly handles DST, timezone offset and everything
            due_local_datetime = local_timezone.localize(due_native_datetime)
            # Convert to UTC
            due_utc_datetime = due_local_datetime.astimezone(pytz.utc)
            self.due = due_utc_datetime

        self.parent = self.find_parent_task()

        # Make parent task dependant on this task
        if self.parent:
            self.parent.add_dependencies |= set([self])

        self.project = self.find_project()

    @property
    def priority_from_tw_format(self):
        return convert_priority_from_tw_format(self.task['priority'])

    @property
    def priority_to_tw_format(self):
        return convert_priority_to_tw_format(self.priority)

    @property
    def due_local_tz_string(self):
        if not self.due:
            return ''

        due_local_datetime = self.due.astimezone(local_timezone)
        return due_local_datetime.strftime(DATETIME_FORMAT)

    @property
    def tainted(self):
        return any([
            self.task['description'] != self.text,
            self.task['priority'] != self.priority_to_tw_format,
            self.task['due'] != self.due,
            self.task['project'] != self.project,
        ])

    def save_to_tw(self):

        # Push the values to the Task only if the Vimwiki representation
        # somehow differs
        # TODO: Check more than description
        if self.tainted:
            self.task['description'] = self.text
            self.task['priority'] = self.priority_to_tw_format
            self.task['due'] = self.due
            # TODO: this does not solve the issue of changed or removed deps (moved task)
            self.task['depends'] |= set(s.task for s in self.add_dependencies
                                        if not s.task.completed)
            # Since project is not updated in vimwiki on change per task, push to TW only
            # if defined
            if self.project:
                self.task['project'] = self.project
            self.task.save()

            # If we saved the task, we need to update. Hooks may have chaned data.
            self.update_from_tw(refresh=False)

        # Load the UUID
        if not self.uuid:
            self.uuid = self.task['uuid']

        # Mark task as done. This works fine with already completed tasks.
        if self.completed and (self.task.pending or self.task.waiting):
            self.task.done()


    def update_from_tw(self, refresh=False):
        if not self.task.saved:
            return

        # We refresh only if specified, since sometimes we
        # know that the TW task is up to date (e.g. because we just
        # loaded the object)
        if refresh:
            self.task.refresh()

        self.text = self.task['description']
        self.priority = self.priority_from_tw_format
        self.completed = (self.task['status'] == u'completed')
        self.due = self.task['due']
        self.project = self.task['project']

    def update_in_buffer(self):
        vim.current.buffer[self.line_number] = str(self)

    def __str__(self):
        return ''.join([
            self.indent,
            '* [',
            'X' if self.completed else self.completed_mark,
            '] ',
            self.text if self.text else 'TEXT MISSING?',
            ' ' + '!' * self.priority if self.priority else '',
            ' ' + self.due_local_tz_string if self.due else '',
            '  #' + self.uuid if self.uuid else '',
        ])

    def find_parent_task(self):
        for i in reversed(range(0, self.line_number)):
            if re.search(GENERIC_TASK, vim.current.buffer[i]):
                task = cache[i]
                if len(task.indent) < len(self.indent):
                    return task

    def find_project(self):
        for i in reversed(range(0, self.line_number)):
            match = re.search(PROJECT_DEFINITION, vim.current.buffer[i])
            if match:
                return match.group('project')


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

