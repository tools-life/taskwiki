# -*- coding: utf-8 -*-
import pytest
from taskwiki import regexp
import re


class TestParsingSyntax(object):
    def test_header(self, test_syntax):
        markup, header_expand = test_syntax
        header = "HEADER1(Test)"
        header = header_expand(header)

        print("Markup: %s,\nHeader syntax:\n%s\nRegex pattern:\n%s" % (
            markup, header, regexp.HEADER[markup].pattern))

        if re.match(regexp.HEADER[markup], header):
            assert 1
        else:
            assert 0

    def test_macro_viewport(self, test_syntax):
        markup, header_expand = test_syntax
        viewport = "HEADER1(Test | project:Home | +home #T $T)"
        viewport = header_expand(viewport)

        print("Viewport syntax:\n%s\nRegex pattern:\n%s" % (
             viewport, regexp.VIEWPORT[markup].pattern))

        match = re.search(regexp.VIEWPORT[markup], viewport)

        assert match != None

        assert match.group('name').strip() == "Test"
        assert match.group('filter').strip() == "project:Home"
        assert match.group('defaults').strip() == "+home"
        assert match.group('source').strip() == "T"
        assert match.group('sort').strip() == "T"
