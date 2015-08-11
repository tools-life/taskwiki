# -*- coding: utf-8 -*-
from datetime import datetime
import sys

# Mock vim to test vim-nonrelated functions
class MockVim(object):

    def eval(*args, **kwargs):
        return 42

    class current(object):
        buffer = ['']

    vars = dict(taskwiki_sort_orders=dict(T='extra'))
    warriors = dict()

mockvim = MockVim()
sys.modules['vim'] = mockvim

from taskwiki.viewport import ViewPort
from taskwiki.viewport import DEFAULT_SORT_ORDER, DEFAULT_VIEWPORT_VIRTUAL_TAGS

class MockCache(object):
    warriors = {'default': 'default', 'T': 'extra'}

cache = MockCache()

class TestParsingVimwikiTask(object):
    def test_simple(self):
        mockvim.current.buffer[0] = "== Test | project:Home =="
        port = ViewPort.from_line(0, cache)

        assert port.taskfilter == DEFAULT_VIEWPORT_VIRTUAL_TAGS + ["project:Home"]
        assert port.name == "Test"
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'default'

    def test_defaults(self):
        mockvim.current.buffer[0] = "== Test | project:Home | +home =="
        port = ViewPort.from_line(0, cache)

        assert port.taskfilter == DEFAULT_VIEWPORT_VIRTUAL_TAGS + ["project:Home"]
        assert port.name == "Test"
        assert port.defaults == {'project':'Home', 'tags':['home']}
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'default'

    def test_different_tw(self):
        mockvim.current.buffer[0] = "== Test | project:Home #T =="
        port = ViewPort.from_line(0, cache)

        assert port.taskfilter == DEFAULT_VIEWPORT_VIRTUAL_TAGS + ["project:Home"]
        assert port.name == "Test"
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'extra'

    def test_different_sort(self):
        mockvim.current.buffer[0] = "== Test | project:Home $T =="
        port = ViewPort.from_line(0, cache)

        assert port.taskfilter == DEFAULT_VIEWPORT_VIRTUAL_TAGS + ["project:Home"]
        assert port.name == "Test"
        assert port.sort == 'extra'
        assert port.tw == 'default'

    def test_different_sort_with_complex_filter(self):
        mockvim.current.buffer[0] = "== Test | project:Home or project:Work $T =="
        port = ViewPort.from_line(0, cache)

        assert port.taskfilter == DEFAULT_VIEWPORT_VIRTUAL_TAGS + ["project:Home", "or", "project:Work"]
        assert port.name == "Test"
        assert port.sort == 'extra'
        assert port.tw == 'default'

    def test_different_sort_tw(self):
        mockvim.current.buffer[0] = "== Test | project:Home #T $T =="
        port = ViewPort.from_line(0, cache)

        assert port.taskfilter == DEFAULT_VIEWPORT_VIRTUAL_TAGS + ["project:Home"]
        assert port.name == "Test"
        assert port.sort == 'extra'
        assert port.tw == 'extra'

    def test_defaults_different_tw(self):
        mockvim.current.buffer[0] = "== Test | project:Home | +home #T =="
        port = ViewPort.from_line(0, cache)

        assert port.taskfilter == DEFAULT_VIEWPORT_VIRTUAL_TAGS + ["project:Home"]
        assert port.name == "Test"
        assert port.defaults == {'project':'Home', 'tags':['home']}
        assert port.sort == DEFAULT_SORT_ORDER
        assert port.tw == 'extra'

    def test_defaults_different_tw_sort(self):
        mockvim.current.buffer[0] = "== Test | project:Home | +home #T $T =="
        port = ViewPort.from_line(0, cache)

        assert port.taskfilter == DEFAULT_VIEWPORT_VIRTUAL_TAGS + ["project:Home"]
        assert port.name == "Test"
        assert port.defaults == {'project':'Home', 'tags':['home']}
        assert port.sort == 'extra'
        assert port.tw == 'extra'
