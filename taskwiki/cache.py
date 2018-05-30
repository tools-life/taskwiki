import vim  # pylint: disable=F0401
import re
import six

from taskwiki import viewport
from taskwiki import regexp
from taskwiki import store
from taskwiki import short
from taskwiki import util
from taskwiki import errors


class BufferProxy(object):

    def __init__(self, number):
        self.data = []
        self.buffer_number = number

    def obtain(self):
        self.data = util.get_buffer(self.buffer_number)[:]

    def push(self):
        with util.current_line_preserved():
            # Only set the buffer contents if the data is changed.
            # Avoids extra undo events with empty diff.
            if util.get_buffer(self.buffer_number)[:] != self.data:
                util.get_buffer(self.buffer_number)[:] = self.data

    def __getitem__(self, index):
        try:
            return self.data[index]
        except IndexError:
            return ''

    def __setitem__(self, index, lines):
        self.data[index] = lines

    def __delitem__(self, index):
        del self.data[index]

    def __iter__(self):
        for line in self.data:
            yield line

    def __len__(self):
        return len(self.data)

    def append(self, data, position=None):
        if position is None:
            self.data.append(data)
        else:
            self.data.insert(position, data)


class CacheRegistry(object):
    """
    Provide a registry for TaskCache instances related to vim buffers.
    """

    def __init__(self):
        # Store caches indexed by buffer number
        self.caches = {}

        # Remember current cache
        self.current_buffer = None

    def __call__(self, buffer_number = None):
        """
        Get cache for given buffer_number or the one which was accessed most recently.
        """

        if buffer_number is None:
            buffer_number = self.current_buffer
        else:
            self.current_buffer = buffer_number

        try:
            # Use existing cache if it was loaded before
            cache = self.caches[buffer_number]
        except KeyError:
            cache = self._load_cache(buffer_number)

        return cache

    def _load_cache(self, buffer_number):
        # Initialize the cache
        cache = TaskCache(buffer_number)
        self.caches[buffer_number] = cache

        # Check the necessary dependencies
        util.enforce_dependencies(cache)

        return cache

    def load_current(self):
        return self(vim.current.buffer.number)


class TaskCache(object):
    """
    A cache that holds all the tasks in the given buffer and prevents
    multiple redundant taskwarrior calls.
    """

    def __init__(self, buffer_number):
        # Determine defaults
        default_rc = util.get_var('taskwiki_taskrc_location') or '~/.taskrc'
        default_data = util.get_var('taskwiki_data_location') or None
        extra_warrior_defs = util.get_var('taskwiki_extra_warriors', {})
        syntax = util.get_var('taskwiki_syntax') or 'default'

        # Handle bytes (vim returnes bytes for Python3)
        if six.PY3:
            default_rc = util.decode_bytes(default_rc)
            default_data = util.decode_bytes(default_data)
            extra_warrior_defs = util.decode_bytes(extra_warrior_defs)
            syntax = util.decode_bytes(syntax)

        # Validate syntax choice and set it
        if syntax in ["default", "markdown", "restructuredtext"]:
            self.syntax = syntax
        else:
            raise errors.TaskWikiException("Syntax '{}' unknown."
                                           .format(syntax))

        # Initialize all the subcomponents
        self.buffer = BufferProxy(buffer_number)
        self.task = store.TaskStore(self)
        self.vwtask = store.VwtaskStore(self)
        self.viewport = store.ViewportStore(self)
        self.line = store.LineStore(self)
        self.warriors = store.WarriorStore(default_rc, default_data, extra_warrior_defs)
        self.buffer_has_authority = True

    @property
    def vimwikitask_dependency_order(self):
        iterated_cache = {
            k:v for k,v in self.vwtask.items()
            if v is not None
        }

        while iterated_cache.keys():
            for key in list(iterated_cache.keys()):
                task = iterated_cache[key]
                if all([t['line_number'] not in iterated_cache.keys()
                        for t in task.add_dependencies]):
                    del iterated_cache[key]
                    yield task

    def reset(self):
        self.buffer.obtain()
        self.task.store = dict()
        self.vwtask.store = dict()
        self.viewport.store = dict()
        self.line.store = dict()

    def load_vwtasks(self, buffer_has_authority=True):
        # Set the authority flag, which determines which data (Buffer or TW)
        # will be considered authoritative
        old_authority = self.buffer_has_authority
        self.buffer_has_authority = buffer_has_authority

        for i in range(len(self.buffer)):
            self.vwtask[i]  # Loads the line into the cache

        # Restore the old authority flag value
        self.buffer_has_authority = old_authority

    def load_viewports(self):
        for i in range(len(self.buffer)):
            port = viewport.ViewPort.from_line(i, self)

            if port is None:
                continue

            port.load_tasks()

            # Save the viewport in the cache
            self.viewport[i] = port

    def update_vwtasks_in_buffer(self):
        for task in self.vwtask.values():
            task.update_in_buffer()

    def save_tasks(self):
        for task in self.vimwikitask_dependency_order:
            task.save_to_tw()

    def load_tasks(self):
        raw_task_info = []

        # Load the tasks in batch, all in given TaskWarrior instance
        for line in self.buffer:
            match = re.search(regexp.GENERIC_TASK, line)
            if not match:
                continue

            tw = self.warriors[match.group('source') or 'default']
            uuid = match.group('uuid')

            if not uuid:
                continue

            raw_task_info.append((uuid, tw))

        for tw in self.warriors.values():
            # Select all tasks in the files that have UUIDs
            uuids = [uuid for uuid, task_tw in raw_task_info if task_tw == tw]

            # If no task in the file contains UUID, we have no job here
            if not uuids:
                continue

            # Get them out of TaskWarrior at once
            tasks = tw.tasks.filter()
            for uuid in uuids:
                tasks = tasks.filter(uuid=uuid)

            # Update each task in the cache
            for task in tasks:
                key = short.ShortUUID(task['uuid'], tw)
                self.task[key] = task

    def update_vwtasks_from_tasks(self):
        for vwtask in self.vwtask.values():
            vwtask.update_from_task()

    def evaluate_viewports(self):
        for port in self.viewport.values():
            port.sync_with_taskwarrior()

    def get_viewport_by_task(self, task):
        """
        Looks for a viewport containing the given task by iterating over the cached
        items.

        Returns the viewport, or None if not found.
        """

        for port in self.viewport.values():
            if task in port.viewport_tasks:
                return port

    def insert_line(self, line, position):
        # Insert the line
        if position == len(self.buffer):
            # Workaround: Necessary since neovim cannot append
            # after the last line of the buffer when mentioning
            # the position explicitly
            self.buffer.append(line)
        else:
            self.buffer.append(line, position)

        # Update the position of all the things shifted by the insertion
        self.vwtask.shift(position, 1)
        self.viewport.shift(position, 1)

        # Shift lines in the line cache
        self.line.shift(position, 1)

    def remove_line(self, position):
        # Remove the line
        del self.buffer[position]

        # Remove the vimwikitask from cache
        del self.vwtask[position]
        del self.viewport[position]

        # Delete the line from the line cache
        del self.line[position]

        # Update the position of all the things shifted by the removal
        self.vwtask.shift(position, -1)
        self.viewport.shift(position, -1)

        # Shift lines in the line cache
        self.line.shift(position, -1)

    def swap_lines(self, position1, position2):
        buffer_size = len(self.buffer)
        if position1 >= buffer_size or position2 >= buffer_size:
            raise ValueError("Tring to swap %d with %d" % (position1, position2))

        # Swap lines in the line cache
        self.line.swap(position1, position2)

        # Swap both the viewport and vimwikitasks indexes
        self.vwtask.swap(position1, position2)
        self.viewport.swap(position1, position2)

    def get_relevant_tw(self):
        # Find closest task
        from taskwiki import vwtask
        task = vwtask.VimwikiTask.find_closest(self)
        return task.tw if task else self.warriors['default']
