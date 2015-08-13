# -*- coding: utf-8 -*-
from datetime import datetime
from base import MockVim, MockCache
import sys

mockvim = MockVim()
sys.modules['vim'] = mockvim

from taskwiki.vwtask import VimwikiTask
from tasklib import local_zone

cache = MockCache()

class TestParsingVimwikiTask(object):
    def setup(self):
        self.mockvim = MockVim()
        sys.modules['vim'] = self.mockvim

    def test_simple(self):
        self.mockvim.current.buffer[0] = "* [ ] This is task description"
        vwtask = VimwikiTask.from_line(cache, 0)

        assert vwtask['description'] == "This is task description"
        assert vwtask['uuid'] == None
        assert vwtask['priority'] == None
        assert vwtask['due'] == None
        assert vwtask['indent'] == ''

    def test_simple_with_unicode(self):
        self.mockvim.current.buffer[0] = "* [ ] This is täsk description"
        vwtask = VimwikiTask.from_line(cache, 0)

        assert vwtask['description'] == u"This is täsk description"
        assert vwtask['uuid'] == None
        assert vwtask['priority'] == None
        assert vwtask['due'] == None
        assert vwtask['indent'] == ''

    def test_due_full(self):
        self.mockvim.current.buffer[0] = "* [ ] Random task (2015-08-08 15:15)"
        vwtask = VimwikiTask.from_line(cache, 0)

        assert vwtask['description'] == u"Random task"
        assert vwtask['due'] == local_zone.localize(datetime(2015,8,8,15,15))
        assert vwtask['uuid'] == None
        assert vwtask['priority'] == None
        assert vwtask['indent'] == ''

    def test_due_short(self):
        self.mockvim.current.buffer[0] = "* [ ] Random task (2015-08-08)"
        vwtask = VimwikiTask.from_line(cache, 0)

        assert vwtask['description'] == u"Random task"
        assert vwtask['due'] == local_zone.localize(datetime(2015,8,8,0,0))
        assert vwtask['uuid'] == None
        assert vwtask['priority'] == None
        assert vwtask['indent'] == ''

    def test_priority_low(self):
        self.mockvim.current.buffer[0] = "* [ ] Semi-Important task !"
        vwtask = VimwikiTask.from_line(cache, 0)

        assert vwtask['description'] == u"Semi-Important task"
        assert vwtask['priority'] == 'L'
        assert vwtask['uuid'] == None

    def test_priority_medium(self):
        self.mockvim.current.buffer[0] = "* [ ] Important task !!"
        vwtask = VimwikiTask.from_line(cache, 0)

        assert vwtask['description'] == u"Important task"
        assert vwtask['priority'] == 'M'
        assert vwtask['uuid'] == None

    def test_priority_high(self):
        self.mockvim.current.buffer[0] = "* [ ] Very important task !!!"
        vwtask = VimwikiTask.from_line(cache, 0)

        assert vwtask['description'] == u"Very important task"
        assert vwtask['priority'] == 'H'
        assert vwtask['uuid'] == None
        assert vwtask['due'] == None

    def test_priority_and_due(self):
        self.mockvim.current.buffer[0] = "* [ ] Due today !!! (2015-08-08)"
        vwtask = VimwikiTask.from_line(cache, 0)

        assert vwtask['description'] == u"Due today"
        assert vwtask['priority'] == 'H'
        assert vwtask['due'] == local_zone.localize(datetime(2015,8,8))
        assert vwtask['uuid'] == None

