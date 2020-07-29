# -*- coding: utf-8 -*-

import re
import textwrap
from itertools import zip_longest
from extra import vwtags


class TagsTest(object):
    wiki_input = None
    expected_output = None
    markup = 'default'

    def test_execute(self):
        wiki_input = textwrap.dedent(self.wiki_input).splitlines()
        got_output = list(vwtags.process(wiki_input, "file.wiki", self.markup))

        if isinstance(self.expected_output, str):
            expected_output = textwrap.dedent(self.expected_output).splitlines()
        else:
            expected_output = self.expected_output

        explanation = {'got_output': got_output, 'expected_output': expected_output}
        for line, (got, expected) in enumerate(zip_longest(got_output, expected_output)):
            explanation['line'] = line
            if hasattr(expected, 'search'):
                assert expected.search(got) is not None, explanation
            else:
                assert got == expected, explanation


class MultiSyntaxTagsTest(TagsTest):

    def test_execute(self, test_syntax):
        markup, header_expand = test_syntax
        self.markup = markup
        self.wiki_input = header_expand(self.wiki_input)

        super(MultiSyntaxTagsTest, self).test_execute()


class TestTagsEmpty(TagsTest):
    wiki_input = ""
    expected_output = ""


class TestTagsBasic(MultiSyntaxTagsTest):
    wiki_input = """\
    HEADER1(a)
    HEADER2(b)
    HEADER2(c)
    HEADER3(d)
    not HEADER2(e)
    HEADER2(f)
    HEADER1(g)
    HEADER3(h)
    """

    expected_output = [
        re.compile(r"^a	file.wiki	/.*/;\"	h	line:1$"),
        re.compile(r"^b	file.wiki	/.*/;\"	h	line:2	header:a$"),
        re.compile(r"^c	file.wiki	/.*/;\"	h	line:3	header:a$"),
        re.compile(r"^d	file.wiki	/.*/;\"	h	line:4	header:a&&&c$"),
        re.compile(r"^f	file.wiki	/.*/;\"	h	line:6	header:a$"),
        re.compile(r"^g	file.wiki	/.*/;\"	h	line:7$"),
        re.compile(r"^h	file.wiki	/.*/;\"	h	line:8	header:g$"),
    ]


class TestTagsViewportsPresets(MultiSyntaxTagsTest):
    wiki_input = """\
    HEADER1(a)
    HEADER2(b | +DUETODAY)
    HEADER2(c || +home)
    HEADER3(d | +OVERDUE | due:today)
    """

    expected_output = [
        re.compile(r"^a	file.wiki	/.*/;\"	h	line:1$"),
        re.compile(r"^b	file.wiki	/.*/;\"	v	line:2	header:a$"),
        re.compile(r"^c	file.wiki	/.*/;\"	p	line:3	header:a$"),
        re.compile(r"^d	file.wiki	/.*/;\"	v	line:4	preset:a&&&c$"),
    ]


class TestTagsVimwikiLinks(TagsTest):
    wiki_input = """\
    = [[link]] =
    == [[li|nk]] ==
    """

    expected_output = """\
    [[link]]	file.wiki	/^= [[link]] =$/;"	h	line:1
    [[li|nk]]	file.wiki	/^== [[li|nk]] ==$/;"	h	line:2	header:[[link]]
    """
