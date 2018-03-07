import re
import six
import itertools
import vim  # pylint: disable=F0401
from datetime import datetime

from tasklib import Task

from taskwiki import regexp
from taskwiki import util
from taskwiki.short import ShortUUID


def convert_priority_from_tw_format(priority):
    return {None: None, 'L': 1, 'M': 2, 'H': 3}[priority]


def convert_priority_to_tw_format(priority):
    return {0: None, 1: 'L', 2: 'M', 3: 'H'}[priority]


class VimwikiTask(object):
    # Lists all data keys that are reflected in Vim representation
    buffer_keys = ('indent', 'description', 'uuid', 'completed_mark',
                   'line_number', 'priority', 'due')

    def __init__(self, cache, uuid, tw):
        """
        Constructs a Vimwiki task from line at given position at the buffer
        """
        self.cache = cache
        self.tw = tw
        self.vim_data = dict(indent='', completed_mark=' ', line_number=None)
        self._buffer_data = None
        self.__unsaved_task = None
        self.uuid = ShortUUID(uuid, self.tw) if uuid is not None else None

    def __getitem__(self, key):
        if key in self.vim_data.keys():
            return self.vim_data[key]
        else:
            return self.task[key]

    def __setitem__(self, key, value):
        if key in self.vim_data.keys():
            self.vim_data[key] = value
        else:
            # Tags require special handling, since we do not want to override,
            # but rather append
            if key == 'tags':
                self.task[key] = self.task[key].union(value)
            else:
                self.task[key] = value


    @classmethod
    def find_closest(cls, cache):
        current_line = util.get_current_line_number()

        # Search lines in order: first all above, than all below
        line_numbers = itertools.chain(
            reversed(range(0, current_line + 1)),
            range(current_line + 1, len(cache.buffer))
            )

        for i in line_numbers:
            vwtask = cls.from_line(cache, i)
            if vwtask:
                return vwtask

    @classmethod
    def parse_line(cls, cache, number):
        return re.search(regexp.GENERIC_TASK, cache.buffer[number])

    @classmethod
    def from_line(cls, cache, number):
        """
        Creates a Vimwiki object from given line in the buffer.
          - If line does not contain a Vimwiki task, returns None.
        """
        # Protected access is ok here
        # pylint: disable=W0212

        match = cache.line[(cls, number)]

        if not match:
            return None

        tw = cache.warriors[match.group('source') or 'default']
        self = cls(cache, match.group('uuid'), tw)

        # Save vim-only related data
        self.vim_data.update({
            'indent': match.group('space'),
            'completed_mark': match.group('completed'),
            'line_number': number,
            })

        # Save task related data into Task object directly
        # Use data from the buffer to update the task only if we
        # explicitly stated that buffer has authority or if the task
        # being loaded is not saved in TW
        if cache.buffer_has_authority or not self.task.saved:
            if six.PY2:
                self.task['description'] = match.group('text').decode('utf-8')
            else:
                self.task['description'] = match.group('text')

            self.task['priority'] = convert_priority_to_tw_format(
                len(match.group('priority') or [])) # This is either 0,1,2 or 3

            # Also make sure changes in the progress field are reflected
            if self['completed_mark'] is 'X':
                self.task['status'] = 'completed'
                self.task['start'] = None
                self.task['end'] = self.task['end'] or datetime.now()
            elif self['completed_mark'] is 'S':
                self.task['status'] = 'pending'
                self.task['start'] = self.task['start'] or datetime.now()
                self.task['end'] = None
            elif self['completed_mark'] == 'D':
                self.task['status'] = 'deleted'
                self.task['start'] = None
                self.task['end'] = self.task['end'] or datetime.now()
            elif self['completed_mark'] == ' ':
                self.task['status'] = "pending"
                self.task['start'] = None
                self.task['end'] = None
                self.task['wait'] = None

            # To get local time aware timestamp, we need to convert to
            # from local datetime to UTC time, since that is what
            # tasklib (correctly) uses
            due = match.group('due')
            if due:
                # With strptime, we get a native datetime object
                parsed_due = None

                try:
                    parsed_due = datetime.strptime(due, regexp.DATETIME_FORMAT)
                except ValueError:
                    try:
                        parsed_due = datetime.strptime(due, regexp.DATE_FORMAT)
                    except ValueError:
                        vim.command('echom "Taskwiki: Invalid timestamp '
                                    'on line %s, ignored."'
                                    % self['line_number'])

                # We need to interpret it as timezone aware object in user's
                # timezone, This properly handles DST and timezone offset.
                if parsed_due:
                    self.task['due'] = parsed_due

            # After all line-data parsing, save the data in the buffer
            self._buffer_data = {key:self[key] for key in self.buffer_keys}

        # We need to track depedency set in a extra attribute, since
        # this may be a new task, and hence it need not to be saved yet.
        # We circumvent this problem by iteration order in the TaskCache
        self.add_dependencies = set()

        self.parent = self.find_parent_task()

        # Make parent task dependant on this task
        if self.parent:
            self.parent.add_dependencies |= set([self])

        # For new tasks, apply defaults from above viewport
        if not self.uuid:
            self.apply_defaults()

            # If -- is in description, assume it's separator for metadata
            # * [ ] this is new task -- project:home
            # should turn into
            # * [ ] this is new task
            # with project:home applied

            if '--' in self['description']:
                first_part, second_part = self['description'].split('--', 1)

                new_description = first_part.strip()
                modstring = second_part.strip()

                # Convert the modstring
                modifications = util.tw_modstring_to_kwargs(modstring)
                for key in modifications.keys():
                    self[key] = modifications[key]

                # Apply the new description
                self['description'] = new_description

        return self

    @classmethod
    def from_task(cls, cache, task):
        self = cls(cache, task['uuid'], task.backend)
        self.update_from_task()

        return self

    @property
    def task(self):
        # New task object accessed second or later time
        if self.__unsaved_task is not None:
            return self.__unsaved_task

        # Return the corresponding task if alrady set
        # Else try to load it or create a new one
        if self.uuid:
            try:
                return self.cache.task[self.uuid]
            except Task.DoesNotExist:
                # Task with stale uuid, recreate
                self.__unsaved_task = Task(self.tw)
                # If task cannot be loaded, we need to remove the UUID
                vim.command(
                    'echom "UUID \'{0}\' not found, Task on line {1} will be '
                    're-created in TaskWarrior."'.format(
                        self.uuid,
                        self['line_number'] + 1
                    ))
                self.uuid = None
        else:
            # New task object accessed first time
            self.__unsaved_task = Task(self.tw)

        return self.__unsaved_task

    @task.setter
    def task(self, task):
        # Make sure we're updating by a correct task
        if task['uuid'] != self.uuid:
            raise ValueError("Task '%s' with '%s' cannot be updated by "
                             "task with uuid '%s'."
                             % (self['description'],
                                self.uuid,
                                task['uuid']))


        self.uuid = ShortUUID(task['uuid'], self.tw)

    @property
    def priority_from_tw_format(self):
        return convert_priority_from_tw_format(self.task['priority'])

    @property
    def priority_to_tw_format(self):
        return convert_priority_to_tw_format(self['priority'])

    def save_to_tw(self):
        # This method persumes all the dependencies have been created at the
        # point it was called, hence move set the dependencies for the underlying
        # task. Remove dependencies for all other tasks within the viewport.

        # This happens so that the dependencies are rebuilt from the tree after
        # each save, since tasks may have been moved within the tree and dependencies
        # added / removed in this implicit manner.
        port = self.cache.get_viewport_by_task(self.task)
        if port is not None:
            self.task['depends'] -= set(port.viewport_tasks)

        self.task['depends'] |= set(s.task for s in self.add_dependencies)

        # Push the values to the Task only if the Vimwiki representation
        # somehow differs
        if self.task.modified or not self.uuid:
            self.task.save()

            # If task was first time saved now, add it to the cache and remove
            # the temporary reference
            if self.__unsaved_task is not None:
                self.uuid = ShortUUID(self.__unsaved_task['uuid'], self.tw)
                self.cache.task[self.uuid] = self.__unsaved_task
                self.__unsaved_task = None

            # If we saved the task, we need to update. Hooks may have changed data.
            self.update_from_task()

    def get_completed_mark(self):
        mark = self['completed_mark']

        if self.task.completed:
            mark = 'X'
        elif mark == 'X':
            mark = ' '

        if self.task.active:
            mark = 'S'
        elif mark == 'S':
            mark = ' '

        if self.task.deleted:
            mark = 'D'
        elif mark == 'D':
            mark = ' '

        if self.task.recurring:
            mark = 'R'
        elif mark == 'R':
            mark = ' '

        if self.task.waiting:
            mark = 'W'
        elif mark == 'W':
            mark = ' '

        return mark

    def update_from_task(self):
        if not self.task.saved:
            return

        self.uuid = ShortUUID(self.task['uuid'], self.tw)
        self['completed_mark'] = self.get_completed_mark()

    def update_in_buffer(self):
        # Look if any of the data that show up in Vim has changed
        buffer_data = {key:self[key] for key in self.buffer_keys}
        if self._buffer_data != buffer_data:
            # If so, update the line in vim and saved buffer data
            self.cache.buffer[self['line_number']] = str(self)
            self._buffer_data = buffer_data

    def __str__(self):
        due_str = ' ' + (
                self['due'].strftime(regexp.DATETIME_FORMAT) if self['due'].time() else
                self['due'].strftime(regexp.DATE_FORMAT)
                ) if self['due'] else ''

        return ''.join([
            self['indent'],
            '* [',
            self['completed_mark'],
            '] ',
            (self['description'].encode('utf-8') if six.PY2 else self['description'])
                if self['description'] else 'TEXT MISSING?',
            ' ' + '!' * self.priority_from_tw_format if self['priority'] else '',
            due_str,
            '  #' + self.uuid.vim_representation(self.cache) if self.uuid else '',
        ])

    def find_parent_task(self):
        # If this task is not indented, we have nothing to do here
        if not self['indent']:
            return None

        for i in reversed(range(0, self['line_number'])):
            # Stop looking if there is less indentation
            indentation = len(self.cache.buffer[i]) - len(self.cache.buffer[i].lstrip())
            indent = self['indent'].replace('\t', '    ')
            if indentation < len(indent):
                # The from_line constructor returns None if line doesn't match a task
                line = self.cache.line[(VimwikiTask, i)]
                if line:
                    return self.cache.vwtask[i]
                else:
                    return None

    def apply_defaults(self):
        from taskwiki import viewport

        for i in reversed(range(0, self['line_number'])):
            port = viewport.ViewPort.from_line(i, self.cache)
            if port:
                # The task should have the same source as the viewport has
                self.tw = port.tw
                self.task.backend = port.tw

                # Any defaults specified should be inherited
                if port.defaults:
                    for key in port.defaults.keys():
                        self[key] = port.defaults[key]

                # If port was detected, break the search
                break

            # If line matches any header that is not a viewport,
            # break the search too
            line = self.cache.buffer[i]
            syntax = self.cache.syntax
            if re.match(regexp.HEADER[syntax], line):
                break
