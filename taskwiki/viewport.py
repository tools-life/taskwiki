import itertools
import re
import vim  # pylint: disable=F0401

import vwtask
import regexp
import util


DEFAULT_VIEWPORT_VIRTUAL_TAGS = ["-DELETED", "-PARENT"]


class ViewPort(object):
    """
    Represents viewport with a given filter.

    A ViewPort is a vimwiki heading which contains (albeit usually hidden
    by the vim's concealing feature) the definition of TaskWarrior filter.

    ViewPort then displays all the tasks that match the given filter below it.

        === Work related tasks | pro:Work ===
        * [ ] Talk with the boss
        * [ ] Publish a new blogpost
          * [ ] Pick a topic
          * [ ] Make sure the hosting is working
    """

    def __init__(self, line_number, cache, tw,
                 name, taskfilter, defaults, meta=None):
        """
        Constructs a ViewPort out of given line.
        """

        self.cache = cache
        self.tw = tw

        self.name = name
        self.line_number = line_number
        self.taskfilter = DEFAULT_VIEWPORT_VIRTUAL_TAGS + taskfilter
        self.defaults = defaults
        self.tasks = set()
        self.meta = meta or dict()

        # Interpret !+DELETED as forcing the +DELETED token (potentionally
        # removing the default +DELETED token from the taskfilter).
        # Interpret !-DELETED as forcint the -DELETED token.
        # Interpret !?DELETED as removing both +DELETED and -DELETED.

        tokens_to_remove = set()
        tokens_to_add = set()

        for token in filter(lambda x: x.isupper(), self.taskfilter):
            if token.startswith('!+'):
                tokens_to_remove.add(token)
                tokens_to_remove.add('-' + token[2:])
                tokens_to_add.add('+' + token[2:])
            elif token.startswith('!-'):
                tokens_to_remove.add(token)
                tokens_to_remove.add('+' + token[2:])
                tokens_to_add.append('-' + token[2:])
            elif token.startswith('!?'):
                tokens_to_remove.add(token)
                tokens_to_remove.add('+' + token[2:])
                tokens_to_remove.add('-' + token[2:])

        self.taskfilter = list(tokens_to_add) + self.taskfilter

        for token in tokens_to_remove:
            if token in self.taskfilter:
                self.taskfilter.remove(token)

        # Deal with the situation when both +TAG and -TAG appear in the
        # taskfilter. If one of them is from the defaults, the explicit
        # version wins.

        def detect_virtual_tag(tag):
            return tag.isupper() and tag[0] in ('+', '-')

        def get_complement_tag(tag):
            return ('+' if tag.startswith('-') else '-') + tag[1:]

        virtual_tags = filter(detect_virtual_tag, self.taskfilter)
        tokens_to_remove = set()

        # For each virtual tag, check if its complement is in the taskfilter too.
        # If so, remove the tag that came from defaults.
        for token in virtual_tags:
            complement = get_complement_tag(token)
            if complement in virtual_tags:
                # Both tag and its complement are in the taskfilter. Remove the
                # one from defaults.
                if token in DEFAULT_VIEWPORT_VIRTUAL_TAGS:
                    tokens_to_remove.add(token)
                if complement in DEFAULT_VIEWPORT_VIRTUAL_TAGS:
                    tokens_to_remove.add(complement)

        for token in tokens_to_remove:
            if token in self.taskfilter:
                self.taskfilter.remove(token)

    @classmethod
    def from_line(cls, number, cache):
        match = re.search(regexp.GENERIC_VIEWPORT, vim.current.buffer[number])

        if not match:
            return None

        taskfilter = util.tw_modstring_to_args(match.group('filter') or '')
        defaults, meta = util.tw_modstring_to_kwargs(
            match.group('filter') + ' ' + (match.group('defaults') or ''))
        name = match.group('name').strip()
        tw = cache.warriors[match.group('source') or 'default']

        self = cls(number, cache, tw, name, taskfilter, defaults, meta)

        return self

    @classmethod
    def find_closest(cls, cache):
        current_line = util.get_current_line_number()

        # Search lines in order: first all above, than all below
        line_numbers = itertools.chain(
            reversed(range(0, current_line + 1)),
            range(current_line + 1, len(vim.current.buffer))
            )

        for i in line_numbers:
            port = cls.from_line(i, cache)
            if port:
                return port

    @property
    def raw_filter(self):
        return ' '.join(self.taskfilter)

    @property
    def raw_defaults(self):
        return ', '.join(
            '{0}:{1}'.format(key, value)
            for key, value in self.defaults.iteritems()
            )

    @property
    def viewport_tasks(self):
        return set(t.task for t in self.tasks)

    @property
    def matching_tasks(self):
        # Split the filter into CLI tokens and filter by the expression
        # By default, do not list deleted tasks
        args = self.taskfilter
        # Visibility tag not set
        if self.meta.get('visible') is None:
            return set(
                task for task in self.tw.tasks.filter(*args)
            )
        # -VISIBLE virtual tag used
        elif self.meta.get('visible') is False:
            # Determine which tasks are outside the viewport
            all_vwtasks = set(self.cache.vimwikitask_cache.values())
            vwtasks_outside_viewport = all_vwtasks - set(self.tasks)
            tasks_outside_viewport = set(
                t.task for t in vwtasks_outside_viewport
                if t is not None
            )

            # Return only those that are not duplicated outside
            # of the viewport
            return set(
                task for task in self.tw.tasks.filter(*args)
                if task not in tasks_outside_viewport
            )

    def get_tasks_to_add_and_del(self):
        # Find the tasks that are new and tasks that are no longer
        # supposed to show up in the viewport
        matching_tasks = self.matching_tasks

        to_add = matching_tasks - self.viewport_tasks
        to_del = self.viewport_tasks - matching_tasks

        return to_add, to_del

    def load_tasks(self):
        # Load all tasks below the viewport
        for i in range(self.line_number + 1, len(vim.current.buffer)):
            line = vim.current.buffer[i]
            match = re.search(regexp.GENERIC_TASK, line)

            if match:
                self.tasks.add(self.cache[i])
            else:
                # If we didn't found a valid task, terminate the viewport
                break

    def sync_with_taskwarrior(self):
        # This is called at the point where all the tasks in the vim
        # are already synced. This should load the tasks from TW matching
        # the filter, and add the tasks that are new. Optionally remove the
        # tasks that are not longer belonging there.

        # Get sets of tasks to add and to delete
        to_add, to_del = self.get_tasks_to_add_and_del()

        # Remove tasks that no longer match the filter
        for task in to_del:
            # Find matching vimwikitasks in the self.tasks set
            # There might be more if the viewport contained multiple
            # representations of the same task
            matching_vimwikitasks= [
                t for t in self.tasks
                if t.uuid == vwtask.ShortUUID(task['uuid'], task.backend)
            ]

            # Remove the tasks from viewport's set and from buffer
            for vimwikitask in matching_vimwikitasks:
                self.tasks.remove(vimwikitask)
                self.cache.remove_line(vimwikitask['line_number'])

        # Add the tasks that match the filter and are not listed
        added_tasks = 0
        existing_tasks = len(self.tasks)

        sorted_to_add = list(to_add)
        sorted_to_add.sort(key=lambda x:x['entry'])

        for task in sorted_to_add:
            added_tasks += 1
            added_at = self.line_number + existing_tasks + added_tasks

            # Add the task object to cache
            self.cache[vwtask.ShortUUID(task['uuid'], self.tw)] = task

            # Create the VimwikiTask
            vimwikitask = vwtask.VimwikiTask.from_task(self.cache, task)
            vimwikitask['line_number'] = added_at
            self.tasks.add(vimwikitask)

            # Update the buffer
            self.cache.insert_line(str(vimwikitask), added_at)

            # Save it to cache
            self.cache[added_at] = vimwikitask

        self.sort_tasks()

    def sort_tasks(self):
        # If there's nothing to sort, we have nothing to do
        if not self.tasks:
            return

        base_offset = min([task['line_number'] for task in self.tasks])

        task_list = list(self.tasks)
        task_list.sort(key=lambda t: t['due'])

        for offset in range(len(task_list)):
            self.cache.swap_lines(base_offset + offset, task_list[offset]['line_number'])

        self.cache.rebuild_vimwikitask_cache()


class TaskCollectionNode(object):
    """
    Stores a collection of VimwikiTasks as tree, where links are defined
    by dependencies.
    """

    def __init__(self, vwtask):
        self.vwtask = vwtask
        self._parent = None
        self.children = []

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        if self.parent is None:
            self._parent = parent
        else:
            raise ValueError("TaskCollectionNode %s cannot have multiple parents" % repr(self))

    def __iter__(self):
        # First return itself
        yield self

        # Then recursilvely iterate in all the children
        for child in self.children:
            for yielded in child:
                yield yielded

    def build_indentation(self, indent):
        self.vwtask['indent'] = ' ' * indent
        self.vwtask.update_in_buffer()

        for child in self.children:
            child.build_indentation(indent + 4)

    def sort(self, sort_func):
        self.children.sort(cmp=lambda x,y: sort_func(x.vwtask.task, y.vwtask.task))

        for child in self.children:
            child.sort(sort_func)

    @property
    def full_list(self):
        full_list = [node for node in self]
        return full_list

    def __repr__(self):
        return u"Node for with ID: {0}".format(self.vwtask.task['id'])
