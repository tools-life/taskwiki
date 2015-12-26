from tasklib import TaskWarrior

import errors


class WarriorStore(object):
    """
    Stores all instances of TaskWarrior objects.
    """

    def __init__(self, default_rc, default_data, extra_warrior_defs):
        default_kwargs = dict(
            data_location=default_data,
            taskrc_location=default_rc,
        )

        # Setup the store of TaskWarrior objects
        self.warriors = {'default': TaskWarrior(**default_kwargs)}

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
        except KeyError:
            raise errors.TaskWikiException(
                "Taskwarrior with key '{0}' not available."
                .format(key))


    def __setitem__(self, key, value):
        self.warriors[key] = value

    def values(self):
        return self.warriors.values()

    def iteritems(self):
        return self.warriors.iteritems()


class NoNoneStore(object):

    def __init__(self, cache):
        self.cache = cache
        self.store = dict()

    def __getitem__(self, key):
        item = self.store.get(key)

        if item is None:
            item = self.get_method(key)

        # If we successfully obtained an item, save it to the cache
        if item is not None:
            self.store[key] = item

        return item  # May return None if the line has no task

    def __setitem__(self, key, value):
        # Never store None in the cache, treat it as deletion
        if value is None:
            if key in self:
                del self[key]
            return

        # Otherwise store the given value
        self.store[key] = value

    def values(self):
        return self.store.values()

    def iteritems(self):
        return self.store.iteritems()

    def clear(self):
        return self.store.clear()


class TaskStore(NoNoneStore):

    def get_method(self, key):
        return key.tw.tasks.get(uuid=key.value)


class VwtaskStore(NoNoneStore):

    def get_method(self, line):
        import vwtask
        return vwtask.VimwikiTask.from_line(self.cache, line)


class ViewportStore(NoNoneStore):

    def get_method(self, line):
        import viewport
        return viewport.ViewPort.from_line(line, self.cache)


class LineStore(NoNoneStore):

    def get_method(self, key):
        cls, line = key
        return cls.parse_line(line)


