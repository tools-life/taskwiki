# -*- coding: utf-8 -*-
import pytest
import re

markup_headers = {
    'default': {
        'HEADER1': "= %s =",
        'HEADER2': "== %s ==",
        'HEADER3': "=== %s ===",
    },
    'markdown': {
        'HEADER1': "# %s",
        'HEADER2': "## %s",
        'HEADER3': "### %s",
    }
}


@pytest.fixture(params=markup_headers)
def test_syntax(request):
    markup = request.param
    format_header_dict = markup_headers[markup]

    def header_expand(string):
        """
        The function perform string replacement of 'HEADER1(.+)' with a header
        syntax for a markup containing the string found in '.+'. This function
        is constructed with a dict of three header levels containing their regex
        and actual syntax.
        When a markup is selected and this function is executed, the function
        will find instance of 'HEADER1' with 1 being any number between 1 and 3
        inclusive.
        """
        for header_level, format_header in format_header_dict.items():
            regex = header_level + '\((.*?)\)'
            string = re.sub(regex,
                            lambda match: format_header % match.group(1),
                            string)
        return string

    return (markup, header_expand)
