import vim
import re

from tasklib.task import TaskWarrior, Task

# Building blocks
BRACKET_OPENING = re.escape('* [')
BRACKET_CLOSING = re.escape('] ')
EMPTY_SPACE = r'(?P<space>\s*)'
UUID_UNNAMED = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
UUID = r'(?P<uuid>{0})'.format(UUID_UNNAMED)
TEXT = r'(?P<text>.+(?!{0}))'.format(UUID_UNNAMED)
DUE = r'(?P<due>\(\d{4}-\d\d-\d\d( \d\d:\d\d)?\))'
COMPLETION_MARK = r'(?P<completed>.)'
UUID_COMMENT = ' #{0}'.format(UUID)
TW_SYNC_MARK = ' #TW'

# Middle building blocks
INCOMPLETE_TASK_PREFIX = EMPTY_SPACE + BRACKET_OPENING + '[^X]' + BRACKET_CLOSING + TEXT

# Final regexps
TASKS_TO_SAVE_TO_TW = ''.join([
    INCOMPLETE_TASK_PREFIX,  # any amount of whitespace followed by uncompleted square
    TEXT,
    '(', DUE, ')?'  # Due is optional
    '(', UUID_COMMENT, '|', TW_SYNC_MARK, ')'   # UUID is not there for new tasks
])

GENERIC_TASK = ''.join([
    EMPTY_SPACE,
    BRACKET_OPENING,
    COMPLETION_MARK,
    BRACKET_CLOSING,
    TEXT,
    '(', DUE, ')?'  # Due is optional
    '(', UUID_COMMENT, '|', TW_SYNC_MARK, ')'   # UUID is not there for new tasks
])


"""
How this plugin works:

    1.) On startup, it reads all the tasks and syncs info TW -> Vimwiki file. Task is identified by their
        uuid.
    2.) When saving, the opposite sync is performed (Vimwiki -> TW direction).
        a) if task is marked as subtask by indentation, the dependency is created between
"""


tw = TaskWarrior()

def get_task(uuid):
    return tw.tasks.get(uuid=uuid)


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

        # First set the task attribute to None, then try to load it, if possible
        self.task = None

        if self.uuid:
            try:
                self.task = tw.tasks.get(uuid=self.uuid)
            except tasklib.task.DoesNotExist:
                pass

    def save_to_tw(self):
        if not self.task:
            self.task = Task(tw)
    
        # Push the values to the Task
        self.task['description'] = self.text
        self.task.save()

        # Load the UUID
        self.task.refresh()
        self.uuid = self.task['uuid']
        vim.command('echom "uuid: %s"' % self.uuid)

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

