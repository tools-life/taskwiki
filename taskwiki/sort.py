from taskwiki import constants
from taskwiki import util

class TaskSorter(object):
    def __init__(self, cache, tasks, sortstring=None):
        self.cache = cache
        self.tasks = tasks
        self.sortstring = (
            sortstring or
            util.get_var('taskwiki_sort_default') or
            constants.DEFAULT_SORT_ORDER
        ) + ',line_number+'

    def execute(self):
        # If there's nothing to sort, we have nothing to do
        if not self.tasks:
            return

        base_offset = min([task['line_number'] for task in self.tasks])

        task_list = list(self.tasks)

        # Create comparator object which will be used to sort the viewport
        comparator = CustomNodeComparator(self.sortstring)

        # Generate the empty nodes
        node_list = [TaskCollectionNode(vwtask, comparator) for vwtask in task_list]

        # Set parents and children for every node
        for node in node_list:
            # Find all children of this node
            node.children = [child for child in node_list
                             if child.vwtask.task in node.vwtask.task['depends']]

            # Set the parent link in the children
            for child in node.children:
                child.parent = node

        root_node_list = [node for node in node_list
                          if node.parent is None]

        root_node_list.sort()

        for node in root_node_list:
            node.sort()

        for node in root_node_list:
            node.build_indentation(0)

        vwtasks_sorted = []
        for node in root_node_list:
            vwtasks_sorted += node.full_list

        for offset in range(len(vwtasks_sorted)):
            self.cache.swap_lines(
                base_offset + offset,
                vwtasks_sorted[offset].vwtask['line_number']
            )


class CustomNodeComparator(object):
    """
    Defines ordering on the TaskCollectionNodes according to the user
    preferences.
    """

    def __init__(self, sortformat):
        self.sort_attrs = []

        for attr_spec in sortformat.split(','):
            # Remove whitespace
            attr_spec = attr_spec.strip()

            # Parse the entry into attr name and reverse flag
            if attr_spec.endswith('+'):
                attr = attr_spec[:-1]
                reverse = False
            elif attr_spec.endswith('-'):
                attr = attr_spec[:-1]
                reverse = True
            else:
                attr = attr_spec
                reverse = False

            self.sort_attrs.append((attr, reverse))

    def generic_compare(self, first, second, method):
        for sort_attr, reverse in self.sort_attrs:
            # Pick the values we are supposed to sort on
            first_value = first.vwtask[sort_attr]
            second_value = second.vwtask[sort_attr]

            # Swap the method of the sort if reversed is True
            if method == 'gt' and reverse == True:
                loop_method = 'lt'
            elif method == 'lt' and reverse == True:
                loop_method = 'gt'
            else:
                loop_method = method

            # Equality on values, continue loop
            if first_value is None and second_value is None:
                continue

            # None values do not respect reverse flags, use method
            if first_value is not None and second_value is None:
                return True if method == 'lt' else False

            if first_value is None and second_value is not None:
                return True if method == 'gt' else False

            # Non-None values should respect reverse flags, use loop_method
            if first_value < second_value:
                return True if loop_method == 'lt' else False
            elif first_value > second_value:
                return True if loop_method == 'gt' else False
            else:
                # Values are equal, move to next distinguisher
                continue

        return True if method == 'eq' else False

    def lt(self, first, second):
        return self.generic_compare(first, second, 'lt')

    def gt(self, first, second):
        return self.generic_compare(first, second, 'gt')

    def eq(self, first, second):
        return self.generic_compare(first, second, 'eq')


class TaskCollectionNode(object):
    """
    Stores a collection of VimwikiTasks as tree, where links are defined
    by dependencies.
    """

    def __init__(self, vwtask, comparator):
        self.vwtask = vwtask
        self._parent = None
        self.children = []
        self.comparator = comparator

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

    def sort(self):
        self.children.sort()

        for child in self.children:
            child.sort()

    @property
    def full_list(self):
        full_list = [node for node in self]
        return full_list

    def __repr__(self):
        return u"Node for with ID: {0}".format(self.vwtask.task['id'] or self.vwtask.task['uuid'])

    def __lt__(self, other):
        return self.comparator.lt(self, other)

    def __gt__(self, other):
        return self.comparator.lt(self, other)

    def __eq__(self, other):
        return self.comparator.lt(self, other)
