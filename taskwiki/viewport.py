import itertools
import re
import six
import sys

from taskwiki import vwtask
from taskwiki import regexp
from taskwiki import errors
from taskwiki import util
from taskwiki import sort
from taskwiki import short
from taskwiki import constants


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

    meta_tokens = ('-VISIBLE',)

    def __init__(self, line_number, cache, tw,
                 name, filterstring, defaultstring, sort=None):
        """
        Constructs a ViewPort out of given line.
        """

        self.cache = cache
        self.tw = tw

        self.name = name
        self.line_number = line_number
        self.taskfilter, self.meta = self.process_filterstring(filterstring)

        if defaultstring:
            self.defaults = util.tw_modstring_to_kwargs(defaultstring)
        else:
            self.defaults = util.tw_args_to_kwargs(self.taskfilter)

        self.tasks = set()
        self.sort = (
            sort or
            util.get_var('taskwiki_sort_order') or
            constants.DEFAULT_SORT_ORDER
        )

    def process_filterstring(self, filterstring):
        """
        This method processes taskfilter in the form or filter string,
        parses it into list of filter args, processing any syntax sugar
        as part of the process.

        Following syntax sugar in filter expressions is currently supported:

        * Expand @name with the definition of 'context.name' TW config
          variable

        * Interpret !+DELETED as forcing the +DELETED token.
        * Interpret !-DELETED as forcing the -DELETED token.
        * Interpret !?DELETED as removing both +DELETED and -DELETED.
        """

        # Get the initial version of the taskfilter args
        taskfilter_args = list(constants.DEFAULT_VIEWPORT_VIRTUAL_TAGS)
        taskfilter_args += "("
        taskfilter_args += util.tw_modstring_to_args(filterstring)
        taskfilter_args += ")"

        # Process syntactic sugar: Context expansion
        detected_contexts = []
        for token in filter(lambda x: x.startswith('@'), taskfilter_args):
            context_variable_name = 'context.{0}'.format(token[1:])
            context_definition = self.tw.config.get(context_variable_name)

            if context_definition:
                context_args = util.tw_modstring_to_args(context_definition)
                detected_contexts.append((token, context_args))
            else:
                raise errors.TaskWikiException("Context definition for '{0}' "
                        "could not be found.".format(token[1:]))

        for context_token, context_args in detected_contexts:
            # Find the position of the context token
            token_index = taskfilter_args.index(context_token)

            # Replace the token at token_index by context_args list
            taskfilter_args = (
                taskfilter_args[:token_index] +
                context_args +
                taskfilter_args[(token_index+1):]
            )

        # Process syntactic sugar: Forcing virtual tags
        tokens_to_remove = set()
        tokens_to_add = set()

        is_forced_virtual_tag = lambda x: x.isupper() and (
            x.startswith('!+') or
            x.startswith('!-') or
            x.startswith('!?')
        )

        for token in filter(is_forced_virtual_tag, taskfilter_args):
            # In any case, remove the forced tag and the forcing
            # flag from the taskfilter
            tokens_to_remove.add(token)
            tokens_to_remove.add('+' + token[2:])
            tokens_to_remove.add('-' + token[2:])

            # Add forced tag versions
            if token.startswith('!+'):
                tokens_to_add.add('+' + token[2:])
            elif token.startswith('!-'):
                tokens_to_add.add('-' + token[2:])
            elif token.startswith('!?'):
                pass

        for token in tokens_to_remove:
            if token in taskfilter_args:
                taskfilter_args.remove(token)

        taskfilter_args = list(tokens_to_add) + taskfilter_args

        # Deal with the situation when both +TAG and -TAG appear in the
        # taskfilter_args. If one of them is from the defaults, the explicit
        # version wins.

        def detect_virtual_tag(tag):
            return tag.isupper() and tag[0] in ('+', '-')

        def get_complement_tag(tag):
            return ('+' if tag.startswith('-') else '-') + tag[1:]

        virtual_tags = list(filter(detect_virtual_tag, taskfilter_args))
        tokens_to_remove = set()
        # For each virtual tag, check if its complement is in the
        # taskfilter_args too. If so, remove the tag that came from defaults.
        for token in virtual_tags:
            complement = get_complement_tag(token)
            if complement in virtual_tags:
                # Both tag and its complement are in the taskfilter_args.
                # Remove the one from defaults.
                if token in constants.DEFAULT_VIEWPORT_VIRTUAL_TAGS:
                    tokens_to_remove.add(token)
                if complement in constants.DEFAULT_VIEWPORT_VIRTUAL_TAGS:
                    tokens_to_remove.add(complement)

        for token in tokens_to_remove:
            if token in taskfilter_args:
                taskfilter_args.remove(token)

        # Process meta tags, remove them from filter
        meta = dict()

        for token in taskfilter_args:
            if token == '-VISIBLE':
                meta['visible'] = False

        taskfilter_args = [x for x in taskfilter_args
                           if x not in self.meta_tokens]

        # If, after all processing, any empty parens appear in the
        # seqeunce of taskfilter_args, remove them
        def deempty_parenthesize(tokens):
            empty_paren_index = None

            # Detect any empty parenthesis pair
            for index, token in enumerate(tokens):
                if token == '(' and tokens[index+1] == ')':
                    empty_paren_index = index

            # Delete empty pair, if found
            if empty_paren_index is not None:
                del tokens[empty_paren_index]
                del tokens[empty_paren_index]

                # Attempt to delete next one, if it exists
                deempty_parenthesize(tokens)

        deempty_parenthesize(taskfilter_args)

        # All syntactic processing done, return the resulting filter args
        return taskfilter_args, meta

    @classmethod
    def parse_line(cls, cache, number):
        return re.search(regexp.VIEWPORT[cache.syntax], cache.buffer[number])

    @classmethod
    def from_line(cls, number, cache):
        match = cache.line[(cls, number)]

        if not match:
            return None

        filterstring = match.group('filter')
        defaults = match.group('defaults')
        name = match.group('name').strip()

        if six.PY2:
            filterstring = filterstring.decode('utf-8')
            defaults = defaults.decode('utf-8') if defaults is not None else defaults
            name = name.decode('utf-8')

        tw = cache.warriors[match.group('source') or 'default']

        sort_id = match.group('sort')
        sorts_configured = util.get_var('taskwiki_sort_orders', {})

        sortstring = None

        # Perform the detection only if specific sort was set
        if sort_id:
            sortstring = sorts_configured.get(sort_id)

            # If we failed to fetch the sortstring, warn the user
            if sortstring is None and sort_id is not None:
                print(u"Sort indicator '{0}' for viewport '{1}' is not defined,"
                       " using default.".format(sort_id, name), sys.stderr)

        self = cls(number, cache, tw, name, filterstring,
                   defaults, sortstring)

        return self

    @classmethod
    def find_closest(cls, cache):
        current_line = util.get_current_line_number()

        # Search lines in order: first all above, than all below
        line_numbers = itertools.chain(
            reversed(range(0, current_line + 1)),
            range(current_line + 1, len(cache.buffer))
            )

        for i in line_numbers:
            port = cls.from_line(i, cache)
            if port:
                return port

    @property
    def raw_filter(self):
        return u' '.join(self.taskfilter)

    @property
    def raw_defaults(self):
        value = u', '.join(
            u'{0}:{1}'.format(key, value)
            for key, value in self.defaults.items()
            )
        # Strip u'' literal symbols from the output
        return value.replace("u'", "'") if six.PY2 else value

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
            all_vwtasks = set(self.cache.vwtask.values())
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
        for i in range(self.line_number + 1, len(self.cache.buffer)):
            line = self.cache.buffer[i]
            match = re.search(regexp.GENERIC_TASK, line)

            if match:
                self.tasks.add(self.cache.vwtask[i])
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
            if task.saved:
                matching_vimwikitasks = [
                    t for t in self.tasks
                    if t.uuid == short.ShortUUID(task['uuid'], task.backend)
                ]
            else:
                # For the tasks that are not saved yet, only one
                # representation can exist, so use object-comparison
                matching_vimwikitasks = [
                    t for t in self.tasks
                    if t.task == task
                ]

            # Remove the tasks from viewport's set and from buffer
            for vimwikitask in matching_vimwikitasks:
                self.tasks.remove(vimwikitask)
                self.cache.remove_line(vimwikitask['line_number'])

        # Add the tasks that match the filter and are not listed
        added_tasks = 0
        existing_tasks = len(self.tasks)

        sorted_to_add = list(to_add)
        sorted_to_add.sort(key=lambda x: x['entry'])

        for task in sorted_to_add:
            added_tasks += 1
            added_at = self.line_number + existing_tasks + added_tasks

            # Add the task object to cache
            self.cache.task[short.ShortUUID(task['uuid'], self.tw)] = task

            # Create the VimwikiTask
            vimwikitask = vwtask.VimwikiTask.from_task(self.cache, task)
            vimwikitask['line_number'] = added_at
            self.tasks.add(vimwikitask)

            # Update the buffer
            self.cache.insert_line(str(vimwikitask), added_at)

            # Save it to cache
            self.cache.vwtask[added_at] = vimwikitask

        sort.TaskSorter(self.cache, self.tasks, self.sort).execute()
