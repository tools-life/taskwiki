# -*- coding: utf-8 -*-
from datetime import datetime
from tests.base import MockVim, MockCacheWithPriorities
import sys

from tasklib import local_zone

class TestParsingVimwikiTask(object):
    def setup(self):
        self.mockvim = MockVim()
        self.cache = MockCacheWithPriorities()
        sys.modules['vim'] = self.mockvim
        from taskwiki.vwtask import VimwikiTask
        self.VimwikiTask = VimwikiTask

    def teardown(self):
        self.cache.reset()

    def test_simple(self):
        self.cache.buffer[0] = "* [ ] This is task description"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == "This is task description"
        assert vwtask['uuid'] == None
        assert vwtask['priority'] == None
        assert vwtask['due'] == None
        assert vwtask['indent'] == ''

    def test_simple_with_unicode(self):
        self.cache.buffer[0] = "* [ ] This is täsk description"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"This is täsk description"
        assert vwtask['uuid'] == None
        assert vwtask['priority'] == None
        assert vwtask['due'] == None
        assert vwtask['indent'] == ''

    def test_due_full(self):
        self.cache.buffer[0] = "* [ ] Random task (2015-08-08 15:15)"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Random task"
        assert vwtask['due'] == local_zone.localize(datetime(2015,8,8,15,15))
        assert vwtask['uuid'] == None
        assert vwtask['priority'] == None
        assert vwtask['indent'] == ''

    def test_due_short(self):
        self.cache.buffer[0] = "* [ ] Random task (2015-08-08)"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Random task"
        assert vwtask['due'] == local_zone.localize(datetime(2015,8,8,0,0))
        assert vwtask['uuid'] == None
        assert vwtask['priority'] == None
        assert vwtask['indent'] == ''

    def test_default_priority_low(self):
        self.cache.buffer[0] = "* [ ] Semi-Important task !"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Semi-Important task"
        assert vwtask['priority'] == 'L'
        assert vwtask['uuid'] == None

    def test_default_priority_medium(self):
        self.cache.buffer[0] = "* [ ] Important task !!"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Important task"
        assert vwtask['priority'] == 'M'
        assert vwtask['uuid'] == None

    def test_default_priority_high(self):
        self.cache.buffer[0] = "* [ ] Very important task !!!"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Very important task"
        assert vwtask['priority'] == 'H'
        assert vwtask['uuid'] == None
        assert vwtask['due'] == None

    def test_custom_priority_0(self):
        self.cache = MockCacheWithPriorities({
            -2: 0, -1: 'L', 0: None, 1: 'M', 2: 'H'
        })
        self.cache.buffer[0] = "* [ ] Very important task ¡¡"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Very important task"
        assert vwtask['priority'] == 0
        assert vwtask['uuid'] == None
        assert vwtask['due'] == None

    def test_custom_priority_L(self):
        self.cache = MockCacheWithPriorities({
            -2: 0, -1: 'L', 0: None, 1: 'M', 2: 'H'
        })
        self.cache.buffer[0] = "* [ ] Very important task ¡"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Very important task"
        assert vwtask['priority'] == 'L'
        assert vwtask['uuid'] == None
        assert vwtask['due'] == None

    def test_custom_priority_none(self):
        self.cache = MockCacheWithPriorities({
            -2: 0, -1: 'L', 0: None, 1: 'M', 2: 'H'
        })
        self.cache.buffer[0] = "* [ ] Very important task"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Very important task"
        assert vwtask['priority'] == None
        assert vwtask['uuid'] == None
        assert vwtask['due'] == None

    def test_custom_priority_M(self):
        self.cache = MockCacheWithPriorities({
            -2: 0, -1: 'L', 0: None, 1: 'M', 2: 'H'
        })
        self.cache.buffer[0] = "* [ ] Very important task !"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Very important task"
        assert vwtask['priority'] == 'M'
        assert vwtask['uuid'] == None
        assert vwtask['due'] == None

    def test_custom_priority_H(self):
        self.cache = MockCacheWithPriorities({
            -2: 0, -1: 'L', 0: None, 1: 'M', 2: 'H'
        })
        self.cache.buffer[0] = "* [ ] Very important task !!"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Very important task"
        assert vwtask['priority'] == 'H'
        assert vwtask['uuid'] == None
        assert vwtask['due'] == None

    def test_custom_priority_no_three_exclamations(self):
        self.cache = MockCacheWithPriorities({
            -2: 0, -1: 'L', 0: None, 1: 'M', 2: 'H'
        })
        self.cache.buffer[0] = "* [ ] Very important task !!!"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Very important task"
        assert vwtask['priority'] == None
        assert vwtask['uuid'] == None
        assert vwtask['due'] == None

    def test_priority_and_due(self):
        self.cache.buffer[0] = "* [ ] Due today !!! (2015-08-08)"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Due today"
        assert vwtask['priority'] == 'H'
        assert vwtask['due'] == local_zone.localize(datetime(2015,8,8))
        assert vwtask['uuid'] == None

    def test_added_modstring(self):
        self.cache.buffer[0] = "* [ ] Home task -- project:Home"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Home task"
        assert vwtask['project'] == u"Home"
        assert vwtask['priority'] == None
        assert vwtask['due'] == None
        assert vwtask['uuid'] == None

    def test_not_modstring(self):
        self.cache.buffer[0] = "* [ ] Task https://somewhere/dash--dash"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Task https://somewhere/dash--dash"
