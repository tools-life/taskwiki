import vim  # pylint: disable=F0401

import vwtask
import viewport

class TaskCache(object):
    """
    A cache that holds all the tasks in the given file and prevents
    multiple redundant taskwarrior calls.
    """

    def __init__(self, tw):
        self.task_cache = dict()
        self.vimwikitask_cache = dict()
        self.tw = tw

    def __getitem__(self, key):
        # String keys refer to the Task objects
        if type(key) in (str, unicode):
            task = self.task_cache.get(key)

            if task is None:
                task = self.tw.tasks.get(uuid=key)
                self.task_cache[key] = task

            return task

        # Integer keys (line numbers) refer to the VimwikiTask objects
        elif type(key) is int:
            vimwikitask = self.vimwikitask_cache.get(key)

            if vimwikitask is None:
                vimwikitask = vwtask.VimwikiTask.from_line(self, key)
                self.vimwikitask_cache[key] = vimwikitask

            return vimwikitask  # May return None if the line has no task

        # Anything else is wrong
        else:
            raise ValueError("Wrong key type: %s (%s)" % (key, type(key)))

    def __setitem__(self, key, value):
        # String keys refer to the Task objects
        if type(key) in (str, unicode):
            self.task_cache[key] = value

        # Integer keys (line numbers) refer to the VimwikiTask objects
        elif type(key) is int:
            self.vimwikitask_cache[key] = value

        # Anything else is wrong
        else:
            raise ValueError("Wrong key type: %s (%s)" % (key, type(key)))

    def __delitem__(self, key):
        # String keys refer to the Task objects
        if type(key) in (str, unicode):
            del self.task_cache[key]

        # Integer keys (line numbers) refer to the VimwikiTask objects
        elif type(key) is int:
            del self.vimwikitask_cache[key]

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

    def load_vwtasks(self):
        for i in range(len(vim.current.buffer)):
            self[i]  # Loads the line into the cache

    def update_buffer(self):
        for task in self.vimwikitask_cache.values():
            if task is None:
                continue

            task.update_in_buffer()

    def save_tasks(self):
        for task in self.vimwikitask_dependency_order:
            task.save_to_tw()

    def load_tasks(self):
        # Select all tasks in the files that have UUIDs
        uuids = [t['uuid'] for t in self.vimwikitask_cache.values()
                 if t is not None and t['uuid'] is not None]

        # If no task in the file contains UUID, we have no job here
        if not uuids:
            return

        # Get them out of TaskWarrior at once
        tasks = self.tw.tasks.filter(uuid=','.join(uuids))

        # Update each task in the cache
        for task in tasks:
            self.task_cache[task['uuid']] = task

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
            if vimwikitask is None:
                continue
            new_cache[vimwikitask['line_number']] = vimwikitask

        self.vimwikitask_cache = new_cache

    def insert_line(self, line, position):
        # Insert the line
        vim.current.buffer.append(line, position)

        # Update the position of all the things shifted by the insertion
        for vimwikitask in self.vimwikitask_cache.values():
            if vimwikitask is None:
                continue

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
            if vimwikitask is None:
                continue

            if vimwikitask['line_number'] >= position:
                vimwikitask['line_number'] -= 1

        # Rebuild cache keys
        self.rebuild_vimwikitask_cache()
