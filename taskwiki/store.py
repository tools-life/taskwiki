from tasklib import TaskWarrior

from taskwiki import errors


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

    def items(self):
        return self.warriors.items()


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
            del self[key]
            return

        # Otherwise store the given value
        self.store[key] = value

    def __delitem__(self, key):
        if key in self.store:
            del self.store[key]

    def __contains__(self, key):
        return key in self.store

    def values(self):
        return self.store.values()

    def items(self):
        return self.store.items()

    def clear(self):
        return self.store.clear()

class LineNumberedKeyedStoreMixin(object):

    def shift(self, position, offset):
        self.store = {
            (i + offset if i >= position else i): self.store[i]
            for i in self.store.keys()
        }

    def swap(self, position1, position2):
        temp = self.store.get(position1)
        self[position1] = self.store.get(position2)
        self[position2] = temp

class TaskStore(NoNoneStore):

    def get_method(self, key):
        return key.tw.tasks.get(uuid=key.value)


class VwtaskStore(LineNumberedKeyedStoreMixin, NoNoneStore):

    def shift(self, position, offset):
        for line, vwtask in self.store.items():
            if line >= position:
                vwtask['line_number'] += offset

        super(VwtaskStore, self).shift(position, offset)

    def swap(self, position1, position2):
        super(VwtaskStore, self).swap(position1, position2)

        for index in (position1, position2):
            if self.store.get(index) is not None:
                self[index]['line_number'] = index

    def get_method(self, line):
        from taskwiki import vwtask
        return vwtask.VimwikiTask.from_line(self.cache, line)


class ViewportStore(LineNumberedKeyedStoreMixin, NoNoneStore):

    def shift(self, position, offset):
        for line, viewport in self.store.items():
            if line >= position:
                viewport.line_number += offset

        super(ViewportStore, self).shift(position, offset)

    def swap(self, position1, position2):
        super(ViewportStore, self).swap(position1, position2)

        for index in (position1, position2):
            if self.store.get(index) is not None:
                self[index].line_number = index

    def get_method(self, line):
        import viewport
        return viewport.ViewPort.from_line(line, self.cache)


class PresetStore(LineNumberedKeyedStoreMixin, NoNoneStore):

    def get_method(self, line):
        import preset
        return preset.PresetHeader.from_line(line, self.cache)


class LineStore(NoNoneStore):

    def __delitem__(self, number):
        for cls, i in list(self.store.keys()):
            if i == number:
                del self.store[(cls, i)]

    def get_method(self, key):
        cls, line = key
        return cls.parse_line(self.cache, line)

    def shift(self, position, offset):
        new_store = {
            (cls, i + offset if i >= position else i): self.store[(cls, i)]
            for cls, i in self.store.keys()
        }

        self.store = new_store

    def swap(self, position1, position2):
        temp_store1 = {
            (cls, i): self.store[(cls, i)]
            for cls, i in self.store.keys()
            if i == position1
        }

        temp_store2 = {
            (cls, i): self.store[(cls, i)]
            for cls, i in self.store.keys()
            if i == position2
        }

        for cls, i in list(self.store.keys()):
            if i == position1 or i == position2:
                del self.store[(cls, i)]

        for cls, i in temp_store1.keys():
            self.store[(cls, position2)] = temp_store1[(cls, i)]

        for cls, i in temp_store2.keys():
            self.store[(cls, position1)] = temp_store2[(cls, i)]

        # Also change the actual line content
        temp = self.cache.buffer[position1]
        self.cache.buffer[position1] = self.cache.buffer[position2]
        self.cache.buffer[position2] = temp


class CompletionStore(NoNoneStore):

    def get_method(self, key):
        from taskwiki import completion
        return completion.Completion(key)
