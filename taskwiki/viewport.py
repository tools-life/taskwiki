import vim

import task
import regexp
from util import parse_tw_arg_string

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

    def __init__(self, line_number, cache, taskfilter, defaults):
        """
        Constructs a ViewPort out of given line.
        """

        self.cache = cache
        self.tw = cache.tw

        self.line_number = line_number
        self.taskfilter = taskfilter
        self.defaults = defaults
        self.tasks = set()

    @classmethod
    def from_line(cls, number, cache):
        match = re.search(regexp.GENERIC_VIEWPORT, vim.current.buffer[number])

        if not match:
            return None

        taskfilter = match.group('filter').strip()
        defaults = parse_tw_arg_string((match.group('defaults') or '').strip())
        self = cls(number, cache, taskfilter, defaults)

        return self

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

        # Split the filter into CLI tokens and filter by the expression
        # By default, do not list deleted tasks
        args = ["-DELETED"] + self.taskfilter.split()
        matching_tasks = set(
            task for task in self.tw.tasks.filter(*args)
        )

        to_add = matching_tasks - set(t.task for t in self.tasks)
        to_del = set(t.task for t in self.tasks) - matching_tasks

        # Remove tasks that no longer match the filter
        for task in to_del:
            # Find matching vimwikitask in the self.tasks set
            [vimwikitask] = [t for t in self.tasks
                             if t['uuid'] == task['uuid']]

            # Remove the task from viewport's set and from buffer
            self.tasks.remove(vimwikitask)
            self.cache.remove_line(vimwikitask['line_number'])

        # Add the tasks that match the filter and are not listed
        added_tasks = 0

        for task in to_add:
            added_tasks += 1
            added_at = self.line_number + len(self.tasks) + added_tasks

            # Add the task object to cache
            self.cache[task['uuid']] = task

            # Create the VimwikiTask
            vimwikitask = task.VimwikiTask.from_task(self.cache, task)
            vimwikitask['line_number'] = added_at

            # Save it to cache
            self.cache[added_at] = vimwikitask

            # Update the buffer
            self.cache.insert_line(str(vimwikitask), added_at)
