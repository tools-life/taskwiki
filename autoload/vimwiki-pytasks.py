import vim
import re

from tasklib.task import TaskWarrior, Task

# Unnamed building blocks
UUID_UNNAMED = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
DUE_UNNAMED = r'\(\d{4}-\d\d-\d\d( \d\d:\d\d)?\)'
SPACE_UNNAMED = r'\s*'
NONEMPTY_SPACE_UNNAMED = r'\s+'
FINAL_SEGMENT_SEPARATOR_UNNAMED = r'(\s+|$)'

TEXT_FORBIDDEN_SUFFIXES = (
    r'\s',  # Text cannot end with whitespace
    r' !', r' !!', r' !!!',  # Any priority value
    DUE_UNNAMED,
    UUID_UNNAMED,  # Text cannot end with UUID
)

# Building blocks
BRACKET_OPENING = re.escape('* [')
BRACKET_CLOSING = re.escape('] ')
EMPTY_SPACE = r'(?P<space>\s*)'
UUID = r'(?P<uuid>{0})'.format(UUID_UNNAMED)
DUE = r'(?P<due>{0})'.format(DUE_UNNAMED)
UUID_COMMENT = '#{0}'.format(UUID)
TEXT = r'(?P<text>.+' + ''.join(['(?<!%s)' % suffix for suffix in TEXT_FORBIDDEN_SUFFIXES])
COMPLETION_MARK = r'(?P<completed>.)'
PRIORITY = r'(?P<priority>!{1,3})'

GENERIC_TASK = re.compile(''.join([
    EMPTY_SPACE,
    BRACKET_OPENING,
    COMPLETION_MARK,
    BRACKET_CLOSING,
    TEXT,
    FINAL_SEGMENT_SEPARATOR_UNNAMED,
    '(', PRIORITY, FINAL_SEGMENT_SEPARATOR_UNNAMED, ')?'
    '(', DUE, FINAL_SEGMENT_SEPARATOR_UNNAMED, ')?'
    '(', UUID_COMMENT, FINAL_SEGMENT_SEPARATOR_UNNAMED, ')?'  # UUID is not there for new tasks
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
                vim.command('echom UUID not found:"%s",'
                            'will be replaced if saved' % self.uuid)
                self.uuid = None
        else:
            self.task = Task(tw)


        self.parent = self.find_parent_task()

        # Make parent task dependant on this task
        if self.parent:
            self.parent.add_dependencies |= set([self])

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
        ])

    def save_to_tw(self):

        # Push the values to the Task only if the Vimwiki representation
        # somehow differs
        # TODO: Check more than description
        if self.tainted:
            self.task['description'] = self.text
            self.task['priority'] = self.priority_to_tw_format
            # TODO: this does not solve the issue of changed or removed deps (moved task)
            self.task['depends'] |= set(s.task for s in self.add_dependencies
                                        if not s.task.completed)
            self.task.save()

        # Load the UUID
        if not self.uuid:
            self.uuid = self.task['uuid']

        # Mark task as done. This works fine with already completed tasks.
        if self.completed and (self.task.pending or self.task.waiting):
            self.task.done()


    def update_from_tw(self, refresh=False):
        if not self.task:
            return

        # We refresh only if specified, since sometimes we
        # know that the TW task is up to date (e.g. because we just
        # loaded the object)
        if refresh:
            self.task.refresh()

        self.text = self.task['description']
        self.priority = self.priority_from_tw_format
        self.completed = (self.task['status'] == u'completed')

    def update_in_buffer(self):
        vim.current.buffer[self.line_number] = str(self)

    def __str__(self):
        return ''.join([
            self.indent,
            '* [',
            'X' if self.completed else self.completed_mark,
            '] ',
            self.text,
            ' ' + '!' * self.priority if self.priority else ''
            '  #',
            self.uuid or 'TW-NOT_SYNCED'
        ])

    def find_parent_task(self):
        for i in reversed(range(0, self.line_number)):
            if re.search(GENERIC_TASK, vim.current.buffer[i]):
                task = cache[i]
                if len(task.indent) < len(self.indent):
                    return task


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


if __name__ == '__main__':
    update_from_tw()

