import re
import six

from taskwiki import regexp
from taskwiki import util

class PresetHeader(object):
    """
        == Taskwiki tasks || project:taskwiki ==
    """

    def __init__(self, cache, parent, level, filterstring, defaultstring):

        self.level = level
        self.parent = parent

        if parent:
            taskfilter = list(parent.taskfilter)
        else:
            taskfilter = []

        if filterstring:
            taskfilter += '('
            taskfilter += util.tw_modstring_to_args(filterstring)
            taskfilter += ')'

        self.taskfilter = taskfilter


        if parent:
            defaults = dict(parent.defaults)
        else:
            defaults = dict()

        if defaultstring:
            defaults.update(util.tw_modstring_to_kwargs(defaultstring))
        else:
            defaults.update(util.tw_args_to_kwargs(taskfilter))

        self.defaults = defaults

    @classmethod
    def parse_line(cls, cache, number):
        header = re.search(regexp.HEADER[cache.markup_syntax],
                           cache.buffer[number])

        if header:
            preset = re.search(regexp.PRESET[cache.markup_syntax],
                               cache.buffer[number])
            if preset:
                return preset

        return header

    @classmethod
    def from_line(cls, number, cache, previous=None):
        match = cache.line[(cls, number)]

        if not match:
            return None

        level = len(match.group('header_start'))

        if level == 1:
            parent = None
        else:
            # Manually get previous header
            if not previous:
                for i in reversed(range(0, number)):
                    previous = cls.from_line(i, cache)
                    if previous:
                        break

            # find parent
            parent = previous
            while parent and parent.level >= level:
                parent = parent.parent

        if parent is None:
            # Create an empty root stub
            parent = cls(cache, None, 0, None, None)


        # use parent object, if no additional filters / defaults are applied
        try:
            filterstring = match.group('filter')
        except IndexError:
            return parent


        defaults = match.group('defaults')

        if six.PY2:
            filterstring = filterstring.decode('utf-8')
            defaults = defaults.decode('utf-8') if defaults is not None else defaults

        self = cls(cache, parent, level, filterstring, defaults)
        return self
