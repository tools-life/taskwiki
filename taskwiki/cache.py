import copy
import vim

from taskwiki.task import VimwikiTask


class TaskCache(object):
    """
    A cache that holds all the tasks in the given file and prevents
    multiple redundant taskwarrior calls.
    """

    def __init__(self, tw):
        self.uuid_cache = dict()
        self.cache = dict()
        self.tw = tw

    def __getitem__(self, key):
        task = self.cache.get(key)

        if task is None:
            task = VimwikiTask(vim.current.buffer[key], key, self.tw, self)
            self.cache[key] = task

            if task.uuid:
                self.uuid_cache[task.uuid] = task

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

#    def update_tasks(self):
#        tasks = [t

