import vim

from taskwiki.task import VimwikiTask

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
            task = VimwikiTask(vim.current.buffer[key], key, self.tw, self)
            self.cache[key] = task

        return task

    def __iter__(self):
#        iterated_cache = {
        while self.cache.keys():
            for key in list(self.cache.keys()):
                task = self.cache[key]
                if all([t.line_number not in self.cache.keys()
                        for t in task.add_dependencies]):
                    del self.cache[key]
                    yield task

    def reset(self):
        self.cache = dict()

#    def update_tasks(self):
#        tasks = [t

