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

    def process_preset_header(self, preset_header, test_syntax):
        """
        Expands the example preset_header to a syntax of a markup and pass on to
        MockVim to be processed.
        The result of the processed preset_header is collected.
        """
        markup, header_expand = test_syntax
        formatted_preset_header = header_expand(preset_header)
        print(formatted_preset_header)

        self.cache.markup_syntax = markup
        self.cache.buffer[0] = formatted_preset_header
        header = self.PresetHeader.from_line(0, self.cache)
        return header

    def test_simple(self, test_syntax):
        preset_header = "HEADER2(Test || project:Home)"
        header = self.process_preset_header(preset_header, test_syntax)

        assert header.taskfilter == ["(", "project:Home", ")"]
        assert header.defaults == {'project': 'Home'}

    def test_defaults(self, test_syntax):
        preset_header = "HEADER2(Test || project:Home || +home)"
        header = self.process_preset_header(preset_header, test_syntax)

        assert header.taskfilter == ["(", "project:Home", ")"]
        assert header.defaults == {'tags': ['home']}
