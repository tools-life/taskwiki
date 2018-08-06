# -*- coding: utf-8 -*-
from tests.base import MockVim, MockCache
import sys


class TestParsingPresetHeader(object):
    def setup(self):
        self.mockvim = MockVim()
        self.cache = MockCache()

        sys.modules['vim'] = self.mockvim
        from taskwiki.preset import PresetHeader
        self.PresetHeader = PresetHeader

    def teardown(self):
        self.mockvim.reset()
        self.cache.reset()

    def test_simple(self):
        self.cache.buffer[0] = "== Test || project:Home =="
        header = self.PresetHeader.from_line(0, self.cache)

        assert header.taskfilter == ["(", "project:Home", ")"]
        assert header.defaults == {'project': 'Home'}

    def test_defaults(self):
        self.cache.buffer[0] = "== Test || project:Home || +home =="
        header = self.PresetHeader.from_line(0, self.cache)

        assert header.taskfilter == ["(", "project:Home", ")"]
        assert header.defaults == {'tags': ['home']}
