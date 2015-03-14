import copy
import vim


class TaskCache(object):
    """
    A cache that holds all the tasks in the given file and prevents
    multiple redundant taskwarrior calls.
    """

    def __init__(self, tw):
        self.cache = dict()
        self.tw = tw

    def __getitem__(self, key):
        task = self.cache.get(key)

        if task is None:
            task = self.tw.tasks.get(uuid=key)
            self.cache[key] = task

        return task

    def __iter__(self):
        iterated_cache = copy.copy(self.cache)
        while iterated_cache.keys():
            for key in list(iterated_cache.keys()):
                task = iterated_cache[key]
                if all([t.line_number not in iterated_cache.keys()
                        for t in task.add_dependencies]):
                    del iterated_cache[key]
                    yield task

    def reset(self):
        self.cache = dict()

    def update_tasks(self):
        # Select all tasks in the files that have UUIDs
        uuids = [t['uuid'] for t in self.cache.values() if t.saved]

        # Get them out of TaskWarrior at once
        tasks = self.tw.filter(uuid=','.join(tasks))

        # Update each task in the cache
        for task in tasks:
            self.cache[task['uuid']] = task

