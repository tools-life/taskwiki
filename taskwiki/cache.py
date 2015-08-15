import vim  # pylint: disable=F0401
import re

import util
import vwtask
import viewport
import regexp

from tasklib import TaskWarrior


class WarriorStore(object):
    """
    Stores all instances of TaskWarrior objects.
    """

    def __init__(self):
        # Determine defaults
        default_rc = vim.vars.get('taskwiki_taskrc_location') or '~/.taskrc'
        default_data = vim.vars.get('taskwiki_data_location') or '~/.task'

        default_kwargs = dict(
            data_location=default_data,
            taskrc_location=default_rc,
        )

        # Setup the store of TaskWarrior objects
        self.warriors = {'default': TaskWarrior(**default_kwargs)}
        extra_warrior_defs = vim.vars.get('taskwiki_extra_warriors', {})

        for key in extra_warrior_defs.keys():
            current_kwargs = default_kwargs.copy()
            current_kwargs.update(extra_warrior_defs[key])
            self.warriors[key] = TaskWarrior(**current_kwargs)

        # Make sure context is not respected in any TaskWarrior
        for tw in self.warriors.values():
            tw.overrides.update({'context':''})

    def __getitem__(self, key):
        try:
            return self.warriors[key]
        except KeyError as e:
            raise util.TaskWikiException(
                "Taskwarrior with key '{0}' not available."
                .format(key))


    def __setitem__(self, key, value):
        self.warriors[key] = value

    def values(self):
        return self.warriors.values()

    def iteritems(self):
        return self.warriors.iteritems()


class TaskCache(object):
    """
    A cache that holds all the tasks in the given file and prevents
    multiple redundant taskwarrior calls.
    """

    def __init__(self):
        self.task_cache = dict()
        self.vimwikitask_cache = dict()
        self.warriors = WarriorStore()
        self.buffer_has_authority = True

    def __getitem__(self, key):
        # Integer keys (line numbers) refer to the VimwikiTask objects
        if type(key) is int:
            vimwikitask = self.vimwikitask_cache.get(key)

            if vimwikitask is None:
                vimwikitask = vwtask.VimwikiTask.from_line(self, key)

            # If we successfully parsed a task, save it to the cache
            if vimwikitask is not None:
                self.vimwikitask_cache[key] = vimwikitask

            return vimwikitask  # May return None if the line has no task

        # ShortUUID objects refer to Task cache
        elif type(key) == vwtask.ShortUUID:
            task = self.task_cache.get(key)

            if task is None:
                task = key.tw.tasks.get(uuid=key.value)
                self.task_cache[key] = task

            return task

        # Anything else is wrong
        else:
            raise ValueError("Wrong key type: %s (%s)" % (key, type(key)))

    def __setitem__(self, key, value):
        # Never store None in the cache, treat it as deletion
        if value is None:
            if key in self:
                del self[key]
            return

        # String keys refer to the Task objects
        if type(key) is vwtask.ShortUUID:
            self.task_cache[key] = value

        # Integer keys (line numbers) refer to the VimwikiTask objects
        elif type(key) is int:
            self.vimwikitask_cache[key] = value

        # Anything else is wrong
        else:
            raise ValueError("Wrong key type: %s (%s)" % (key, type(key)))

    def __delitem__(self, key):
        # String keys refer to the Task objects
        if type(key) is vwtask.ShortUUID:
            del self.task_cache[key]

        # Integer keys (line numbers) refer to the VimwikiTask objects
        elif type(key) is int:
            del self.vimwikitask_cache[key]

        # Anything else is wrong
        else:
            raise ValueError("Wrong key type: %s (%s)" % (key, type(key)))

    def __contains__(self, key):
        # String keys refer to the Task objects
        if type(key) is vwtask.ShortUUID:
            return key in self.task_cache

        # Integer keys (line numbers) refer to the VimwikiTask objects
        elif type(key) is int:
            return key in self.vimwikitask_cache

        # Anything else is wrong
        else:
            raise ValueError("Wrong key type: %s (%s)" % (key, type(key)))

    @property
    def vimwikitask_dependency_order(self):
        iterated_cache = {
            k:v for k,v in self.vimwikitask_cache.iteritems()
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
        self.task_cache = dict()
        self.vimwikitask_cache = dict()

    def load_vwtasks(self, buffer_has_authority=True):
        # Set the authority flag, which determines which data (Buffer or TW)
        # will be considered authoritative
        old_authority = self.buffer_has_authority
        self.buffer_has_authority = buffer_has_authority

        for i in range(len(vim.current.buffer)):
            self[i]  # Loads the line into the cache

        # Restore the old authority flag value
        self.buffer_has_authority = old_authority

    def update_vwtasks_in_buffer(self):
        for task in self.vimwikitask_cache.values():
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
                self.task_cache[key] = task

    def update_vwtasks_from_tasks(self):
        for vwtask in self.vimwikitask_cache.values():
            vwtask.update_from_task()

    def evaluate_viewports(self):
        i = 0
        while i < len(vim.current.buffer):
            port = viewport.ViewPort.from_line(i, self)
            i += 1

            if port is None:
                continue

            port.load_tasks()
            port.sync_with_taskwarrior()

    def rebuild_vimwikitask_cache(self):
        new_cache = dict()

        for vimwikitask in self.vimwikitask_cache.values():
            new_cache[vimwikitask['line_number']] = vimwikitask

        self.vimwikitask_cache = new_cache

    def insert_line(self, line, position):
        # Insert the line
        vim.current.buffer.append(line, position)

        # Update the position of all the things shifted by the insertion
        for vimwikitask in self.vimwikitask_cache.values():
            if vimwikitask['line_number'] >= position:
                vimwikitask['line_number'] += 1

        # Rebuild cache keys
        self.rebuild_vimwikitask_cache()

    def remove_line(self, position):
        # Remove the line
        del vim.current.buffer[position]

        # Remove the vimwikitask from cache
        del self.vimwikitask_cache[position]

        # Update the position of all the things shifted by the removal
        for vimwikitask in self.vimwikitask_cache.values():
            if vimwikitask['line_number'] > position:
                vimwikitask['line_number'] -= 1

        # Rebuild cache keys
        self.rebuild_vimwikitask_cache()

    def swap_lines(self, position1, position2):
        buffer_size = len(vim.current.buffer)
        if position1 >= buffer_size or position2 >= buffer_size:
            raise ValueError("Tring to swap %d with %d" % (position1, position2))

        # Swap both the lines and vimwikitasks indexes
        temp = vim.current.buffer[position2]
        vim.current.buffer[position2] = vim.current.buffer[position1]
        vim.current.buffer[position1] = temp

        temp = self[position2]
        self[position2] = self.vimwikitask_cache.get(position1)
        self[position1] = temp

        # Update the line numbers cached in the vimwikitasks
        for position in (position1, position2):
            if self[position] is not None:
                self[position]['line_number'] = position

        # Rebuild of the cache is not necessary, only those two lines are affected

    def get_relevant_tw(self):
        # Find closest task
        task = vwtask.VimwikiTask.find_closest(self)
        return task.tw if task else self.warriors['default']
