# -*- coding: utf-8 -*-
from datetime import datetime
from tests.base import MockVim, MockCache
import sys

from taskwiki.constants import DEFAULT_SORT_ORDER, DEFAULT_VIEWPORT_VIRTUAL_TAGS


class TestParsingVimwikiTask(object):
    def setup(self):
        self.mockvim = MockVim()
        self.cache = MockCache()

        # Setup fake entries for custom TaskWarrior instance and Sort order
        self.cache.warriors.update({'T': 'extra'})
        self.mockvim.vars.update({'taskwiki_sort_orders': dict(T='extra')})

        sys.modules['vim'] = self.mockvim
        from taskwiki.viewport import ViewPort
        self.ViewPort = ViewPort

    def teardown(self):
        self.mockvim.reset()
        self.cache.reset()

    def process_viewport(self, viewport, test_syntax):
        """
        Expands the example viewport to a syntax of a markup and pass on to
        MockVim to be processed.
        The result of the processed viewport is collected.
        """
        markup, header_expand = test_syntax
        formatted_viewport = header_expand(viewport)

        self.cache.markup_syntax = markup
        self.cache.buffer[0] = formatted_viewport
        port = self.ViewPort.from_line(0, self.cache)
        return port

    def test_simple(self, test_syntax):
        example_viewport = "HEADER2(Test | project:Home)"
        port = self.process_viewport(example_viewport, test_syntax)

        assert port.taskfilter == list(DEFAULT_VIEWPORT_VIRTUAL_TAGS) + ["(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'default'

    def test_defaults(self, test_syntax):
        example_viewport = "HEADER2(Test | project:Home | +home)"
        port = self.process_viewport(example_viewport, test_syntax)

        assert port.taskfilter == list(DEFAULT_VIEWPORT_VIRTUAL_TAGS) + ["(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.defaults == {'tags':['home']}
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'default'

    def test_different_tw(self, test_syntax):
        example_viewport = "HEADER2(Test | project:Home #T)"
        port = self.process_viewport(example_viewport, test_syntax)

        assert port.taskfilter == list(DEFAULT_VIEWPORT_VIRTUAL_TAGS) + ["(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'extra'

    def test_different_sort(self, test_syntax):
        example_viewport = "HEADER2(Test | project:Home $T)"
        port = self.process_viewport(example_viewport, test_syntax)

        assert port.taskfilter == list(DEFAULT_VIEWPORT_VIRTUAL_TAGS) + ["(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.sort == 'extra'
        assert port.tw == 'default'

    def test_different_sort_with_complex_filter(self, test_syntax):
        example_viewport = "HEADER2(Test | project:Home or project:Work $T)"
        port = self.process_viewport(example_viewport, test_syntax)

        assert port.taskfilter == list(DEFAULT_VIEWPORT_VIRTUAL_TAGS) + ["(", "project:Home", "or", "project:Work", ")"]
        assert port.name == "Test"
        assert port.sort == 'extra'
        assert port.tw == 'default'

    def test_different_sort_tw(self, test_syntax):
        example_viewport = "HEADER2(Test | project:Home #T $T)"
        port = self.process_viewport(example_viewport, test_syntax)

        assert port.taskfilter == list(DEFAULT_VIEWPORT_VIRTUAL_TAGS) + ["(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.sort == 'extra'
        assert port.tw == 'extra'

    def test_defaults_different_tw(self, test_syntax):
        example_viewport = "HEADER2(Test | project:Home | +home #T)"
        port = self.process_viewport(example_viewport, test_syntax)

        assert port.taskfilter == list(DEFAULT_VIEWPORT_VIRTUAL_TAGS) + ["(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.defaults == {'tags':['home']}
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'extra'

    def test_defaults_different_tw_sort(self, test_syntax):
        example_viewport = "HEADER2(Test | project:Home | +home #T $T)"
        port = self.process_viewport(example_viewport, test_syntax)

        assert port.taskfilter == list(DEFAULT_VIEWPORT_VIRTUAL_TAGS) + ["(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.defaults == {'tags':['home']}
        assert port.sort == 'extra'
        assert port.tw == 'extra'

    def test_override_default_virtual_tags_neutral(self, test_syntax):
        example_viewport = "HEADER2(Test | project:Home !?DELETED)"
        port = self.process_viewport(example_viewport, test_syntax)

        assert port.taskfilter == ["-PARENT", "(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.defaults == {'project':'Home'}
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'default'

    def test_override_default_virtual_tags_positive(self, test_syntax):
        example_viewport = "HEADER2(Test | project:Home !+DELETED)"
        port = self.process_viewport(example_viewport, test_syntax)

        assert port.taskfilter == ["+DELETED", "-PARENT", "(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.defaults == {'project':'Home'}
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'default'

    def test_override_default_virtual_tags_negative(self, test_syntax):
        example_viewport = "HEADER2(Test | project:Home !-DELETED)"
        port = self.process_viewport(example_viewport, test_syntax)

        assert port.taskfilter == ["-DELETED", "-PARENT", "(", "project:Home", ")"]
        assert port.name == "Test"
        assert port.defaults == {'project':'Home'}
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'default'

    def test_override_default_virtual_tags_positive_without_forcing(self, test_syntax):
        example_viewport = "HEADER2(Test | project:Home +DELETED)"
        port = self.process_viewport(example_viewport, test_syntax)

        assert port.taskfilter == ["-PARENT", "(", "project:Home", "+DELETED", ")"]
        assert port.name == "Test"
        assert port.defaults == {'project':'Home'}
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'default'
