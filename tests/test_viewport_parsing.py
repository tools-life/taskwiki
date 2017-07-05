# -*- coding: utf-8 -*-
from datetime import datetime
from tests.base import MockVim, MockCache
import sys

from taskwiki.constants import DEFAULT_SORT_ORDER, DEFAULT_VIEWPORT_VIRTUAL_TAGS

syntax_header = {
    'default': "== Test | %s ==",
    'markdown': "## Test | %s",
    'restructuredtext': "Test | %s\n================",
}
syntax_choice = 'default'

class TestParsingVimwikiTask(object):
    def setup(self):
        self.mockvim = MockVim()
        self.cache = MockCache()

        # Setup fake entries for custom TaskWarrior instance and Sort order
        self.cache.warriors.update({'T': 'extra'})
        self.mockvim.vars.update({'taskwiki_sort_orders': dict(T='extra')})

        # Set syntax
        self.cache.syntax = syntax_choice

        sys.modules['vim'] = self.mockvim
        from taskwiki.viewport import ViewPort
        self.ViewPort = ViewPort

    def teardown(self):
        self.mockvim.reset()
        self.cache.reset()

    def test_simple(self):
        self.cache.buffer[0] = syntax_header[syntax_choice] % "project:Home"
        port = self.ViewPort.from_line(0, self.cache)

        assert port.taskfilter == list(DEFAULT_VIEWPORT_VIRTUAL_TAGS) + ["(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'default'

    def test_defaults(self):
        self.cache.buffer[0] = syntax_header[syntax_choice] % "project:Home | +home"
        port = self.ViewPort.from_line(0, self.cache)

        assert port.taskfilter == list(DEFAULT_VIEWPORT_VIRTUAL_TAGS) + ["(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.defaults == {'tags':['home']}
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'default'

    def test_different_tw(self):
        self.cache.buffer[0] = syntax_header[syntax_choice] % "project:Home #T"
        port = self.ViewPort.from_line(0, self.cache)

        assert port.taskfilter == list(DEFAULT_VIEWPORT_VIRTUAL_TAGS) + ["(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'extra'

    def test_different_sort(self):
        self.cache.buffer[0] = syntax_header[syntax_choice] % "project:Home $T"
        port = self.ViewPort.from_line(0, self.cache)

        assert port.taskfilter == list(DEFAULT_VIEWPORT_VIRTUAL_TAGS) + ["(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.sort == 'extra'
        assert port.tw == 'default'

    def test_different_sort_with_complex_filter(self):
        self.cache.buffer[0] = syntax_header[syntax_choice] % "project:Home or project:Work $T"
        port = self.ViewPort.from_line(0, self.cache)

        assert port.taskfilter == list(DEFAULT_VIEWPORT_VIRTUAL_TAGS) + ["(", "project:Home", "or", "project:Work", ")"]
        assert port.name == "Test"
        assert port.sort == 'extra'
        assert port.tw == 'default'

    def test_different_sort_tw(self):
        self.cache.buffer[0] = syntax_header[syntax_choice] % "project:Home #T $T"
        port = self.ViewPort.from_line(0, self.cache)

        assert port.taskfilter == list(DEFAULT_VIEWPORT_VIRTUAL_TAGS) + ["(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.sort == 'extra'
        assert port.tw == 'extra'

    def test_defaults_different_tw(self):
        self.cache.buffer[0] = syntax_header[syntax_choice] % "project:Home | +home #T"
        port = self.ViewPort.from_line(0, self.cache)

        assert port.taskfilter == list(DEFAULT_VIEWPORT_VIRTUAL_TAGS) + ["(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.defaults == {'tags':['home']}
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'extra'

    def test_defaults_different_tw_sort(self):
        self.cache.buffer[0] = syntax_header[syntax_choice] % "project:Home | +home #T $T"
        port = self.ViewPort.from_line(0, self.cache)

        assert port.taskfilter == list(DEFAULT_VIEWPORT_VIRTUAL_TAGS) + ["(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.defaults == {'tags':['home']}
        assert port.sort == 'extra'
        assert port.tw == 'extra'

    def test_override_default_virtual_tags_neutral(self):
        self.cache.buffer[0] = syntax_header[syntax_choice] % "project:Home !?DELETED"
        port = self.ViewPort.from_line(0, self.cache)

        assert port.taskfilter == ["-PARENT", "(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.defaults == {'project':'Home'}
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'default'

    def test_override_default_virtual_tags_positive(self):
        self.cache.buffer[0] = syntax_header[syntax_choice] % "project:Home !+DELETED"
        port = self.ViewPort.from_line(0, self.cache)

        assert port.taskfilter == ["+DELETED", "-PARENT", "(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.defaults == {'project':'Home'}
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'default'

    def test_override_default_virtual_tags_negative(self):
        self.cache.buffer[0] = syntax_header[syntax_choice] % "project:Home !-DELETED"
        port = self.ViewPort.from_line(0, self.cache)

        assert port.taskfilter == ["-DELETED", "-PARENT", "(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.defaults == {'project':'Home'}
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'default'

    def test_override_default_virtual_tags_positive_without_forcing(self):
        self.cache.buffer[0] = syntax_header[syntax_choice] % "project:Home +DELETED"
        port = self.ViewPort.from_line(0, self.cache)

        assert port.taskfilter == ["-PARENT", "(", "project:Home", "+DELETED", ")"]
        assert port.name == "Test"
        assert port.defaults == {'project':'Home'}
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'default'
