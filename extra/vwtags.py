#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys

if __name__ == '__main__':
    path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, path)

from taskwiki import regexp


def match_header(line, syntax):
    m = re.search(regexp.VIEWPORT[syntax], line)
    if m:
        return 'viewport', m

    m = re.search(regexp.PRESET[syntax], line)
    if m:
        return 'preset', m

    m = re.search(regexp.HEADER[syntax], line)
    if m:
        return 'header', m

    return None, None


def process(file_content, filename, syntax):
    parents = [None] * 6
    for lnum, line in enumerate(file_content):
        cur_kind_long, m = match_header(line, syntax)
        if not m:
            continue

        cur_lvl = len(m.group('header_start')) - 1
        cur_tag = m.group('name').strip()
        cur_searchterm = "^" + m.group(0).rstrip("\r\n") + "$"
        cur_kind = cur_kind_long[0]

        assert cur_lvl < len(parents)
        parents[cur_lvl] = cur_kind_long, cur_tag
        for i in range(cur_lvl + 1, len(parents)):
            parents[i] = None

        parent_scopes = [p for p in parents[0:cur_lvl] if p]
        scope = "&&&".join([tag for _, tag in parent_scopes])
        if scope:
            parent_kind, _ = parent_scopes[-1]
            scope = "\t" + parent_kind + ":" + scope

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
