#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

help_text = """
Extracts tags from Vimwiki files. Useful for the Tagbar plugin.

Usage:
Install Tagbar (http://majutsushi.github.io/tagbar/). Then, put this file
anywhere and add the following to your .vimrc:

let g:tagbar_type_vimwiki = {
          \   'ctagstype':'vimwiki'
          \ , 'kinds':['h:header']
          \ , 'sro':'&&&'
          \ , 'kind2scope':{'h':'header'}
          \ , 'sort':0
          \ , 'ctagsbin':'/path/to/vwtags.py'
          \ , 'ctagsargs': 'default'
          \ }

The value of ctagsargs must be one of 'default', 'markdown' or 'media',
whatever syntax you use. However, if you use multiple wikis with different
syntaxes, you can, as a workaround, use the value 'all' instead. Then, Tagbar
will show markdown style headers as well as default/mediawiki style headers,
but there might be erroneously shown headers.
"""

import sys
import re

if len(sys.argv) < 3:
    print(help_text)
    exit()

syntax = sys.argv[1]
filename = sys.argv[2]
rx_default_media = r"^\s*(={1,6})([^=].*[^=])\1\s*$"
rx_markdown = r"^\s*(#{1,6})([^#].*)$"

if syntax in ("default", "media"):
    rx_header = re.compile(rx_default_media)
elif syntax == "markdown":
    rx_header = re.compile(rx_markdown)
else:
    rx_header = re.compile(rx_default_media + "|" + rx_markdown)

file_content = []
try:
    with open(filename, "r") as vim_buffer:
        file_content = vim_buffer.readlines()
except:
    exit()

state = [""]*6
for lnum, line in enumerate(file_content):

    match_header = rx_header.match(line)

    if not match_header:
        continue

    match_lvl = match_header.group(1) or match_header.group(3)
    match_tag = match_header.group(2) or match_header.group(4)

    cur_lvl = len(match_lvl)
    cur_tag = match_tag.strip()
    cur_searchterm = "^" + match_header.group(0).rstrip("\r\n") + "$"
    cur_kind = "h"

    state[cur_lvl-1] = cur_tag
    for i in range(cur_lvl, 6):
        state[i] = ""

    scope = "&&&".join(
            [state[i] for i in range(0, cur_lvl-1) if state[i] != ""])
    if scope:
        scope = "\theader:" + scope

    print('{0}\t{1}\t/{2}/;"\t{3}\tline:{4}{5}'.format(
        cur_tag, filename, cur_searchterm, cur_kind, str(lnum+1), scope))
