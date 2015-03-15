import datetime
import vim

from regexp import *
from tasklib.task import Task, SerializingObject


def convert_priority_from_tw_format(priority):
    return {None: 0, 'L': 1, 'M': 2, 'H': 3}[priority]


def convert_priority_to_tw_format(priority):
    return {0: None, 1: 'L', 2: 'M', 3: 'H'}[priority]


class VimwikiTask(object):
    def __init__(self, cache):
        """
        Constructs a Vimwiki task from line at given position at the buffer
        """
        self.cache = cache
        self.tw = cache.tw
        self._task = None

    @classmethod
    def from_line(cls, cache, number):
        """
        Creates a Vimwiki object from given line in the buffer.
          - If line does not contain a Vimwiki task, returns None.
        """

        match = re.search(GENERIC_TASK, line)

        if not match:
            return None

        self = cls(cache)

        self.indent = match.group('space')
        self.text = match.group('text')
        self.uuid = match.group('uuid')  # can be None for new tasks
        self.due = match.group('due')  # TODO: convert to proper timestamp
        self.completed_mark = match.group('completed')
        self.completed = self.completed_mark is 'X'
        self.line_number = number
        self.priority = len(match.group('priority') or []) # This is either 0,1,2 or 3

        # To get local time aware timestamp, we need to convert to from local datetime
        # to UTC time, since that is what tasklib (correctly) uses
        if self.due:
            # With strptime, we get a native datetime object
            try:
                parsed_due = datetime.strptime(self.due, DATETIME_FORMAT)
            except ValueError:
                try:
                    parsed_due = datetime.strptime(self.due, DATE_FORMAT)
                except ValueError:
                    vim.command('echom "Taskwiki: Invalid timestamp on line %s, '
                                'ignored."' % self.line_number)

            # We need to interpret it as timezone aware object in user's timezone
            # This properly handles DST, timezone offset and everything
            self.due = SerializingObject().datetime_normalizer(parsed_due)

        # We need to track depedency set in a extra attribute, since
        # this may be a new task, and hence it need not to be saved yet.
        # We circumvent this problem by iteration order in the TaskCache
        self.add_dependencies = set()

        self.parent = self.find_parent_task()

        # Make parent task dependant on this task
        if self.parent:
            self.parent.add_dependencies |= set([self])

        self.project = self.find_project()

    @property
    def task(self):
        # Return the corresponding task if alrady set
        if self._task is not None:
            return self._task

        # Else try to load it or create a new one
        if self.uuid:
            try:
                self._task = self.tw.tasks.get(uuid=self.uuid)
            except Task.DoesNotExist:
                self._task = Task(self.tw)
                # If task cannot be loaded, we need to remove the UUID
                vim.command('echom "UUID not found: %s,'
                            'will be replaced if saved"' % self.uuid)
                self.uuid = None
        else:
            self._task = Task(self.tw)

        return self._task

    @task.setter
    def task(self, task):
        # Make sure we're updating by a correct task
        if task['uuid'] != self.uuid:
            raise ValueError("Task '%s' with '%s' cannot be updated by "
                             "task with uuid '%s'."
                             % (self.text, self.uuid, task['uuid']))

        self._task = task

    @property
    def priority_from_tw_format(self):
        return convert_priority_from_tw_format(self.task['priority'])

    @property
    def priority_to_tw_format(self):
        return convert_priority_to_tw_format(self.priority)

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

    def update_from_tw(self):
        if not self.task.saved:
            return

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
            ' ' + self.due.strftime(DATETIME_FORMAT) if self.due else '',
            '  #' + self.uuid if self.uuid else '',
        ])

    def find_parent_task(self):
        for i in reversed(range(0, self.line_number)):
            if re.search(GENERIC_TASK, vim.current.buffer[i]):
                task = self.cache[i]
                if len(task.indent) < len(self.indent):
                    return task

    def find_project(self):
        for i in reversed(range(0, self.line_number)):
            match = re.search(PROJECT_DEFINITION, vim.current.buffer[i])
            if match:
                return match.group('project')
