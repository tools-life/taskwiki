import vim
import re

from tasklib.task import TaskWarrior, Task

# Unnamed building blocks
UUID_UNNAMED = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
SPACE_UNNAMED = r'\s*'
NONEMPTY_SPACE_UNNAMED = r'\s+'
FINAL_SEGMENT_SEPARATOR_UNNAMED = r'(\s+|$)'

# Building blocks
BRACKET_OPENING = re.escape('* [')
BRACKET_CLOSING = re.escape('] ')
EMPTY_SPACE = r'(?P<space>\s*)'
UUID = r'(?P<uuid>{0})'.format(UUID_UNNAMED)
TEXT = r'(?P<text>.+(?<!{0}))'.format(UUID_UNNAMED)
DUE = r'(?P<due>\(\d{4}-\d\d-\d\d( \d\d:\d\d)?\))'
COMPLETION_MARK = r'(?P<completed>.)'
UUID_COMMENT = '#{0}'.format(UUID)

# Middle building blocks
INCOMPLETE_TASK_PREFIX = EMPTY_SPACE + BRACKET_OPENING + '[^X]' + BRACKET_CLOSING + TEXT

# Final regexps
TASKS_TO_SAVE_TO_TW = ''.join([
    INCOMPLETE_TASK_PREFIX,  # any amount of whitespace followed by uncompleted square
    FINAL_SEGMENT_SEPARATOR_UNNAMED,
    '(', DUE, FINAL_SEGMENT_SEPARATOR_UNNAMED, ')?'  # Due is optional
    '(', UUID_COMMENT, FINAL_SEGMENT_SEPARATOR_UNNAMED, ')?'   # UUID is not there for new tasks
])

GENERIC_TASK = re.compile(''.join([
    EMPTY_SPACE,
    BRACKET_OPENING,
    COMPLETION_MARK,
    BRACKET_CLOSING,
    TEXT,
    FINAL_SEGMENT_SEPARATOR_UNNAMED,
    '(', DUE, FINAL_SEGMENT_SEPARATOR_UNNAMED, ')?'  # Due is optional
    '(', UUID_COMMENT, FINAL_SEGMENT_SEPARATOR_UNNAMED, ')?'   # UUID is not there for new tasks
]))


"""
How this plugin works:

    1.) On startup, it reads all the tasks and syncs info TW -> Vimwiki file. Task is identified by their
        uuid.
    2.) When saving, the opposite sync is performed (Vimwiki -> TW direction).
        a) if task is marked as subtask by indentation, the dependency is created between
"""


tw = TaskWarrior()

class TaskCache(object):
    def __init__(self):
        self.cache = dict()

    def __getitem__(self, key):
        task = self.cache.get(key)

        if task is None:
            task = VimwikiTask(vim.current.buffer[key], key)
            self.cache[key] = task

        return task

    def __iter__(self):
        while self.cache.keys():
            for key in list(self.cache.keys()):
                task = self.cache[key]
                if all([t.line_number not in self.cache.keys()
                        for t in task.add_dependencies]):
                    del self.cache[key]
                    yield task

    def reset(self):
        self.cache = dict()

cache = TaskCache()


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
        else:
            self.task = Task(tw)


        self.parent = self.find_parent_task()

        # Make parent task dependant on this task
        if self.parent:
            self.parent.add_dependencies |= set([self])

    def save_to_tw(self):

        # Push the values to the Task only if the Vimwiki representation
        # somehow differs
        # TODO: Check more than description
        if self.task['description'] != self.text:
            self.task['description'] = self.text
            self.task['depends'] |= set(s.task for s in self.add_dependencies
                                        if not s.task.completed)
            self.task.save()

        # Load the UUID
        if not self.uuid:
            self.uuid = self.task['uuid']

        # Mark task as done. This works fine with already completed tasks.
        if self.completed:
            self.task.done()

    def update_from_tw(self):
        if not self.task:
            return

        self.task.refresh()
        self.text = self.task['description']
        # TODO: update due
        self.completed = (self.task['status'] == u'completed')

    def __str__(self):
        self.update_from_tw()

        return ''.join([
            self.indent,
            '* [',
            'X' if self.completed else self.completed_mark,
            '] ',
            self.text,
            '  #',
            self.uuid or 'TW-NOT_SYNCED'
        ])

    def find_parent_task(self):
        for i in reversed(range(0, self.line_number)):
            if re.search(TASKS_TO_SAVE_TO_TW, vim.current.buffer[i]):
                task = VimwikiTask(line, i)
                if len(task.indent) < len(self.indent):
                    return task


def load_update_incomplete_tasks():
    """
    Updates all the incomplete tasks in the vimwiki file if the info from TW is different.
    """

    for i in range(len(vim.current.buffer)):
        line = vim.current.buffer[i]

        if re.search(TASKS_TO_SAVE_TO_TW, line):
            task = VimwikiTask(line, i)
            task.save_to_tw()
            line = str(task)

        vim.current.buffer[i] = line

    number_of_lines = len(vim.current.buffer)
    vim.command('echom "lines: %d"' % number_of_lines)

if __name__ == '__main__':
    load_update_incomplete_tasks()

