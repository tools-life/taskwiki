import re
import itertools
import vim  # pylint: disable=F0401
from datetime import datetime

from tasklib import Task
import regexp
import viewport
import util


def convert_priority_from_tw_format(priority):
    return {None: None, 'L': 1, 'M': 2, 'H': 3}[priority]


def convert_priority_to_tw_format(priority):
    return {0: None, 1: 'L', 2: 'M', 3: 'H'}[priority]


class ShortUUID(object):
    def __init__(self, value, tw):
        # Extract the UUID from the given object. Support both
        # strings and ShortUUID instances.
        if type(value) in (str, unicode):
            # Use str reprentation of the value, first 8 chars
            self.value = str(value)[:8]
        elif type(value) is ShortUUID:
            self.value = value.value
        else:
            raise ValueError("Incorrect type for ShortUUID: {0}"
                             .format(type(value)))

        self.tw = tw

    def __eq__(self, other):
        # For full UUIDs, our value is shorter
        # For short, the lengths are the same
        if not isinstance(other, ShortUUID):
            return False

        return other.value == self.value and self.tw == other.tw

    def __hash__(self):
        return self.value.__hash__() * 17 + self.tw.__hash__() * 7

    def __str__(self):
        return self.value

    def vim_representation(self, cache):
        """
        Return 'H:<uuid>' for TW with indicator 'H',
        '<uuid>' for default instance.
        """

        # Determine the key of the TW instance
        [key] = [key for key, value in cache.warriors.iteritems()
                 if value == self.tw]
        prefix = '{0}:'.format(key) if key is not 'default' else ''

        # Return the H:<uuid> or <uuid> value
        return '{0}{1}'.format(prefix, self.value)


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
            self.task[key] = value

    @classmethod
    def find_closest(cls, cache):
        current_line = util.get_current_line_number()

        # Search lines in order: first all above, than all below
        line_numbers = itertools.chain(
            reversed(range(0, current_line + 1)),
            range(current_line + 1, len(vim.current.buffer))
            )

        for i in line_numbers:
            vwtask = cls.from_line(cache, i)
            if vwtask:
                return vwtask

    @classmethod
    def from_current_line(cls, cache):
        line_number = util.get_current_line_number()
        return cls.from_line(cache, line_number)

    @classmethod
    def from_line(cls, cache, number):
        """
        Creates a Vimwiki object from given line in the buffer.
          - If line does not contain a Vimwiki task, returns None.
        """
        # Protected access is ok here
        # pylint: disable=W0212

        match = re.search(regexp.GENERIC_TASK, vim.current.buffer[number])

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
            self.task['description'] = match.group('text').decode('utf-8')
            self.task['priority'] = convert_priority_to_tw_format(
                len(match.group('priority') or [])) # This is either 0,1,2 or 3

            # Also make sure changes in the progress field are reflected
            if self['completed_mark'] is 'X':
                self.task['status'] = 'completed'
            elif self['completed_mark'] is 'S':
                self.task['status'] = 'pending'
                self.task['start'] = self.task['start'] or 'now'

            # To get local time aware timestamp, we need to convert to
            # from local datetime to UTC time, since that is what
            # tasklib (correctly) uses
            due = match.group('due')
            if due:
                # With strptime, we get a native datetime object
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
                return self.cache[self.uuid]
            except Task.DoesNotExist:
                # Task with stale uuid, recreate
                self.__unsaved_task = Task(self.tw)
                # If task cannot be loaded, we need to remove the UUID
                vim.command(
                    'echom "UUID \'{0}\' not found, Task on line {1} will be '
                    're-created in TaskWarrior."'.format(
                        self.uuid,
                        self['line_number']
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

    @property
    def tainted(self):
        return self.task.modified or self.add_dependencies

    def save_to_tw(self):
        # Push the values to the Task only if the Vimwiki representation
        # somehow differs
        # TODO: Check more than description
        if self.tainted or not self.uuid:
            # TODO: this does not solve the issue of changed or removed deps (moved task)
            self.task['depends'] |= set(s.task for s in self.add_dependencies
                                        if not s.task.completed)
            self.task.save()

            # If task was first time saved now, add it to the cache and remove
            # the temporary reference
            if self.__unsaved_task is not None:
                self.uuid = ShortUUID(self.__unsaved_task['uuid'], self.tw)
                self.cache[self.uuid] = self.__unsaved_task
                self.__unsaved_task = None

            # Mark task as done.
            is_not_completed = self.task.pending or self.task.waiting
            if self['completed_mark'] == 'X' and is_not_completed:
                self.task.done()

            # If we saved the task, we need to update. Hooks may have chaned data.
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
            vim.current.buffer[self['line_number']] = str(self)
            self._buffer_data = buffer_data

    def __str__(self):
        return ''.join([
            self['indent'],
            '* [',
            self['completed_mark'],
            '] ',
            self['description'].encode('utf-8') if self['description'] else 'TEXT MISSING?',
            ' ' + '!' * self.priority_from_tw_format if self['priority'] else '',
            ' ' + self['due'].strftime(regexp.DATETIME_FORMAT) if self['due'] else '',
            '  #' + self.uuid.vim_representation(self.cache) if self.uuid else '',
        ])

    def find_parent_task(self):
        for i in reversed(range(0, self['line_number'])):
            # The from_line constructor returns None if line doesn't match a task
            task = self.cache[i]
            if task and len(task['indent']) < len(self['indent']):
                return task

    def apply_defaults(self):
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
