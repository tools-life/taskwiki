#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re

rx_default_media = r"^\s*(={1,6})([^=].*[^=])\1\s*$"
rx_markdown = r"^\s*(#{1,6})([^#].*)$"


def process(file_content, filename, syntax):
    if syntax in ("default", "media"):
        rx_header = re.compile(rx_default_media)
    elif syntax == "markdown":
        rx_header = re.compile(rx_markdown)
    else:
        rx_header = re.compile(rx_default_media + "|" + rx_markdown)

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

        yield('{0}\t{1}\t/{2}/;"\t{3}\tline:{4}{5}'.format(
            cur_tag, filename, cur_searchterm, cur_kind, str(lnum+1), scope))


if __name__ == '__main__':
    if len(sys.argv) < 3:
        exit()

    syntax = sys.argv[1]
    filename = sys.argv[2]

    file_content = []
    try:
        with open(filename, "r") as vim_buffer:
            file_content = vim_buffer.readlines()
    except:
        exit()

    for output in process(file_content, filename, syntax):
        print(output)
