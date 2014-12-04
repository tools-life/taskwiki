import vim
import re
from tasklib import task

"""
How this plugin works:

    1.) On startup, it reads all the tasks and syncs info TW -> Vimwiki file. Task is identified by their
        uuid.
    2.) When saving, the opposite sync is performed (Vimwiki -> TW direction).
        a) if task is marked as subtask by indentation, the dependency is created between
"""

INCOMPLETE_TASK_REGEXP = (
    "\v\* \[[^X]\].*"  # any amount of whitespace followed by uncompleted square
    # Any of the following:
    "(\(\d{4}-\d\d-\d\d( \d\d:\d\d)?\)" # Timestamp
    "|#TW\s*$" # Task indicator (insert this to have the task added)
    "|#[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"  # Task UUID 
)

TASK_REGEXP = '#TW'

tw = task.TaskWarrior()

class Random(object):
    attr = 'Ta dpc'

r = Random()

def get_task(uuid):
    return tw.tasks.get(uuid=uuid)

def load_tasks():
    valid_tasks = [line for line in vim.current.buffer if re.search(TASK_REGEXP, line)]

    for line in valid_tasks:
        vim.command('echom "%s"' % line)

    r.attr = 'Whoohoooo'

def RandomExample():
    vim.command('echom "volame daco"')
    vim.command('echom "%s"' % r.attr)

def RandomExample3():
    r.attr = r.attr + 'XO'
    vim.command('echom "Random example 3"')

if __name__ == '__main__':
    load_tasks()

