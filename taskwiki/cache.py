import vim  # pylint: disable=F0401
import re

import vwtask
import viewport
import regexp
import store


class TaskCache(object):
    """
    A cache that holds all the tasks in the given file and prevents
    multiple redundant taskwarrior calls.
    """

    def __init__(self):
        # Determine defaults
        default_rc = vim.vars.get('taskwiki_taskrc_location') or '~/.taskrc'
        default_data = vim.vars.get('taskwiki_data_location') or '~/.task'
        extra_warrior_defs = vim.vars.get('taskwiki_extra_warriors', {})

        self.task = store.TaskStore(self)
        self.vwtask = store.VwtaskStore(self)
        self.viewport = store.ViewportStore(self)
        self.line = store.LineStore(self)
        self.warriors = store.WarriorStore(default_rc, default_data, extra_warrior_defs)
        self.buffer_has_authority = True

    @property
    def vimwikitask_dependency_order(self):
        iterated_cache = {
            k:v for k,v in self.vwtask.iteritems()
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
        self.task.store = dict()
        self.vwtask.store = dict()
        self.viewport.store = dict()
        self.line.store = dict()

    def load_vwtasks(self, buffer_has_authority=True):
        # Set the authority flag, which determines which data (Buffer or TW)
        # will be considered authoritative
        old_authority = self.buffer_has_authority
        self.buffer_has_authority = buffer_has_authority

        for i in range(len(vim.current.buffer)):
            self.vwtask[i]  # Loads the line into the cache

        # Restore the old authority flag value
        self.buffer_has_authority = old_authority

    def load_viewports(self):
        for i in range(len(vim.current.buffer)):
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
        for line in vim.current.buffer:
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
                key = vwtask.ShortUUID(task['uuid'], tw)
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
        if position == len(vim.current.buffer):
            # Workaround: Necessary since neovim cannot append
            # after the last line of the buffer when mentioning
            # the position explicitly
            vim.current.buffer.append(line)
        else:
            vim.current.buffer.append(line, position)

        # Update the position of all the things shifted by the insertion
        self.vwtask.shift(position, 1)
        self.viewport.shift(position, 1)

        # Shift lines in the line cache
        self.line.shift(position, 1)

    def remove_line(self, position):
        # Remove the line
        del vim.current.buffer[position]

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
        buffer_size = len(vim.current.buffer)
        if position1 >= buffer_size or position2 >= buffer_size:
            raise ValueError("Tring to swap %d with %d" % (position1, position2))

        # Swap lines in the line cache
        self.line.swap(position1, position2)

        # Swap both the viewport and vimwikitasks indexes
        self.vwtask.swap(position1, position2)
        self.viewport.swap(position1, position2)

    def get_relevant_tw(self):
        # Find closest task
        task = vwtask.VimwikiTask.find_closest(self)
        return task.tw if task else self.warriors['default']
