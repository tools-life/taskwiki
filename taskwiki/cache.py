import copy
import vim


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
                vimwikitask = VimwikiTask.from_line(self, key)
                return vimwikitask  # May return None if the line has no task
        # Anything else is wrong
        else:
            raise ValueError("Wrong key type: %s (%s)" % (key, type(key)))

    def iterate_vimwiki_tasks(self):
        iterated_cache = copy.copy(self.task_cache)
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

    def update_tasks(self):
        # Select all tasks in the files that have UUIDs
        uuids = [t['uuid'] for t in self.task_cache.values() if t.saved]

        # Get them out of TaskWarrior at once
        tasks = self.tw.filter(uuid=','.join(tasks))

        # Update each task in the cache
        for task in tasks:
            self.task_cache[task['uuid']] = task

