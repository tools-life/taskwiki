# -*- coding: utf-8 -*-
import pytest
from taskwiki import regexp
import re
from tests.base import header_expand


class TestParsingSyntax(object):
    def test_header(self, test_syntax):
        markup, format_header = test_syntax
        header = format_header % 'Test'

        print("Markup: %s,\nHeader syntax:\n%s\nRegex pattern:\n%s" % (
            markup, header, regexp.HEADER[markup].pattern))

        if re.match(regexp.HEADER[markup], header):
            assert 1
        else:
            assert 0


    def test_viewport(self, test_syntax):
        markup, format_header = test_syntax
        viewport = format_header % "Test | project:Home | +home #T $T"

        print("Markup: %s\nViewport syntax:\n%s\nRegex pattern:\n%s" % (
            markup, viewport, regexp.VIEWPORT[markup].pattern))

        match = re.search(regexp.VIEWPORT[markup], viewport)

        assert match != None

        assert match.group('name').strip() == "Test"
        assert match.group('filter').strip() == "project:Home"
        assert match.group('defaults').strip() == "+home"
        assert match.group('source').strip() == "T"
        assert match.group('sort').strip() == "T"


    def test_macro_viewport(self, test_syntax):
        markup, format_header = test_syntax
        viewport = "HEADER(Test | project:Home | +home #T $T)"
        viewport = header_expand(viewport, format_header)

        print("Viewport syntax:\n%s\nRegex pattern:\n%s" % (
             viewport, regexp.VIEWPORT[markup].pattern))

        match = re.search(regexp.VIEWPORT[markup], viewport)

        assert match != None

        assert match.group('name').strip() == "Test"
        assert match.group('filter').strip() == "project:Home"
        assert match.group('defaults').strip() == "+home"
        assert match.group('source').strip() == "T"
        assert match.group('sort').strip() == "T"

