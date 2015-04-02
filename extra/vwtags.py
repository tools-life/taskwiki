#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import re

if len(sys.argv) < 3:
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

result = []
state = [""]*6
for lnum, line in enumerate(file_content):

    match_header = rx_header.match(line)

    if not match_header:
        continue

    match_lvl = match_header.group(1) or match_header.group(3)
    match_tag = match_header.group(2) or match_header.group(4)

    cur_lvl = len(match_lvl)
    cur_tag = match_tag.split('|')[0].strip()
    cur_searchterm = "^" + match_header.group(0).rstrip("\r\n") + "$"
    cur_kind = "h" if not '|' in line else "v"

    state[cur_lvl-1] = cur_tag
    for i in range(cur_lvl, 6):
        state[i] = ""

    scope = "&&&".join(
            [state[i] for i in range(0, cur_lvl-1) if state[i] != ""])
    if scope:
        scope = "\theader:" + scope

    result.append([cur_tag, filename, cur_searchterm, cur_kind, str(lnum+1), scope])

for i in range(len(result)):
    if i != len(result) - 1:
        if len(result[i+1][5]) <= len(result[i][5]) and len(result[i][5]) != 0:
            result[i][3] = 'i'

    print('{0}\t{1}\t/{2}/;"\t{3}\tline:{4}{5}'.format(
        result[i][0],
        result[i][1],
        result[i][2],
        result[i][3],
        result[i][4],
        result[i][5],
        ))
