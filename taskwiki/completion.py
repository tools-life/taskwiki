from functools import reduce, wraps
import re

from tasklib import TaskWarrior

from taskwiki import constants
from taskwiki import regexp


def complete_last_word(f):
    @wraps(f)
    def wrapper(self, arglead):
        before, sep, after = arglead.rpartition(' ')
        comps = f(self, after)
        if comps:
            return [before + sep + comp for comp in comps]
        else:
            return []
    return wrapper


# TODO(2023-06-27): use functools once python 3.7 is EOL
def cached_property(f):
    @wraps(f)
    def wrapper(self):
        k = '_cache_' + f.__name__
        if k in self.__dict__:
            return self.__dict__[k]
        else:
            v = f(self)
            self.__dict__[k] = v
            return v
    return wrapper


# "must*opt" -> "must(o(p(t)?)?)?"
def prefix_regex(s):
    must, _, opt = s.partition('*')
    return must + reduce(lambda y, x: f"({x}{y})?", reversed(opt), '')


RE_PROJECT = re.compile(prefix_regex('pro*ject'))
RE_DATE = re.compile('|'.join(
    [prefix_regex(r)
     for r in "du*e un*til wa*it ent*ry end st*art sc*heduled".split()]))
RE_RECUR = re.compile(prefix_regex('re*cur'))


class Completion():
    def __init__(self, tw):
        self.tw = tw

    @cached_property
    def _attributes(self):
        return sorted(self.tw.execute_command(['_columns']))

    @cached_property
    def _tags(self):
        if self.tw.version < TaskWarrior.VERSION_2_4_5:
            return sorted(self.tw.execute_command(['_tags']))
        else:
            return sorted(set(
                tag
                for tags in self.tw.execute_command(['_unique', 'tag'])
                for tag in tags.split(',')))

    @cached_property
    def _projects(self):
        if self.tw.version < TaskWarrior.VERSION_2_4_5:
            return sorted(self.tw.execute_command(['_projects']))
        else:
            return sorted(self.tw.execute_command(['_unique', 'project']))

    def _complete_any(self, w):
        if w:
            return []

        return ['+', '-'] + [attr + ':' for attr in self._attributes()]

    def _complete_attributes(self, w):
        if not w.isalpha():
            return []

        return [attr + ':'
                for attr in self._attributes()
                if attr.startswith(w)]

    def _complete_tags(self, w):
        if not w or w[0] not in ['+', '-']:
            return []

        t = w[1:]
        return [w[0] + tag
                for tag in self._tags()
                if tag.startswith(t)]

    def _comp_words(self, w, pattern, words):
        before, sep, after = w.partition(':')
        if not sep or not re.fullmatch(pattern, before):
            return []

        return [before + sep + word
                for word in words()
                if word.startswith(after)]

    def _complete_projects(self, w):
        return self._comp_words(w, RE_PROJECT, self._projects)

    def _complete_dates(self, w):
        return self._comp_words(w, RE_DATE, lambda: constants.COMPLETION_DATE)

    def _complete_recur(self, w):
        return self._comp_words(w, RE_RECUR, lambda: constants.COMPLETION_RECUR)

    @complete_last_word
    def modify(self, w):
        return \
            self._complete_any(w) or \
            self._complete_attributes(w) or \
            self._complete_projects(w) or \
            self._complete_tags(w) or \
            self._complete_dates(w) or \
            self._complete_recur(w) or \
            []

    def omni_modstring_findstart(self, line):
        m = re.search(regexp.GENERIC_TASK, line)
        bline = line.encode("utf-8")  # omni findstart needs byte offset
        if m and not m.group('uuid') and b' -- ' in bline:
            return bline.rfind(b' ') + 1
        else:
            return -1

    def omni_modstring(self, w):
        return \
            self._complete_any(w) or \
            self._complete_attributes(w) or \
            self._complete_projects(w) or \
            self._complete_tags(w) or \
            self._complete_dates(w) or \
            self._complete_recur(w) or \
            []
