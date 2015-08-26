# -*- coding: utf-8 -*-
from datetime import datetime
from base import MockVim, MockCache
import sys

from tasklib import local_zone

class TestParsingVimwikiTask(object):
    def setup(self):
        self.mockvim = MockVim()
        self.cache = MockCache()
        sys.modules['vim'] = self.mockvim
        from taskwiki.vwtask import VimwikiTask
        self.VimwikiTask = VimwikiTask

    def teardown(self):
        self.mockvim.reset()
        self.cache.reset()

    def test_simple(self):
        self.mockvim.current.buffer[0] = "* [ ] This is task description"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == "This is task description"
        assert vwtask['uuid'] == None
        assert vwtask['priority'] == None
        assert vwtask['due'] == None
        assert vwtask['indent'] == ''

    def test_simple_with_unicode(self):
        self.mockvim.current.buffer[0] = "* [ ] This is täsk description"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"This is täsk description"
        assert vwtask['uuid'] == None
        assert vwtask['priority'] == None
        assert vwtask['due'] == None
        assert vwtask['indent'] == ''

    def test_due_full(self):
        self.mockvim.current.buffer[0] = "* [ ] Random task (2015-08-08 15:15)"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Random task"
        assert vwtask['due'] == local_zone.localize(datetime(2015,8,8,15,15))
        assert vwtask['uuid'] == None
        assert vwtask['priority'] == None
        assert vwtask['indent'] == ''

    def test_due_short(self):
        self.mockvim.current.buffer[0] = "* [ ] Random task (2015-08-08)"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Random task"
        assert vwtask['due'] == local_zone.localize(datetime(2015,8,8,0,0))
        assert vwtask['uuid'] == None
        assert vwtask['priority'] == None
        assert vwtask['indent'] == ''

    def test_priority_low(self):
        self.mockvim.current.buffer[0] = "* [ ] Semi-Important task !"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Semi-Important task"
        assert vwtask['priority'] == 'L'
        assert vwtask['uuid'] == None

    def test_priority_medium(self):
        self.mockvim.current.buffer[0] = "* [ ] Important task !!"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Important task"
        assert vwtask['priority'] == 'M'
        assert vwtask['uuid'] == None

    def test_priority_high(self):
        self.mockvim.current.buffer[0] = "* [ ] Very important task !!!"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Very important task"
        assert vwtask['priority'] == 'H'
        assert vwtask['uuid'] == None
        assert vwtask['due'] == None

    def test_priority_and_due(self):
        self.mockvim.current.buffer[0] = "* [ ] Due today !!! (2015-08-08)"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Due today"
        assert vwtask['priority'] == 'H'
        assert vwtask['due'] == local_zone.localize(datetime(2015,8,8))
        assert vwtask['uuid'] == None

    def test_added_modstring(self):
        self.mockvim.current.buffer[0] = "* [ ] Home task -- project:Home"
        vwtask = self.VimwikiTask.from_line(self.cache, 0)

        assert vwtask['description'] == u"Home task"
        assert vwtask['project'] == u"Home"
        assert vwtask['priority'] == None
        assert vwtask['due'] == None
        assert vwtask['uuid'] == None
