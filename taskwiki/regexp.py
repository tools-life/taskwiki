import re

# Unnamed building blocks
UUID_UNNAMED = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
UUID_UNNAMED_SHORT = r'[0-9a-fA-F]{8}'
DUE_UNNAMED = r'\(\d{4}-\d\d-\d\d( \d\d:\d\d)?\)'
SPACE_UNNAMED = r'\s*'
NONEMPTY_SPACE_UNNAMED = r'\s+'
FINAL_SEGMENT_SEPARATOR_UNNAMED = r'(\s+|$)'
SOURCE_INDICATOR = r'(?P<source>[A-Z]):'

# Building blocks
BRACKET_OPENING = re.escape('* [')
BRACKET_CLOSING = re.escape('] ')
EMPTY_SPACE = r'(?P<space>\s*)'
UUID = r'(?P<uuid>{0}|{1})'.format(UUID_UNNAMED, UUID_UNNAMED_SHORT)
DUE = r'(?P<due>{0})'.format(DUE_UNNAMED)
TEXT = r'(?P<text>.+?)'
COMPLETION_MARK = r'(?P<completed>.)'
PRIORITY = r'(?P<priority>!{1,3})'

GENERIC_TASK = re.compile(''.join([
    '^',
    EMPTY_SPACE,
    BRACKET_OPENING,
    COMPLETION_MARK,
    BRACKET_CLOSING,
    TEXT,
    FINAL_SEGMENT_SEPARATOR_UNNAMED,
    '(', PRIORITY, FINAL_SEGMENT_SEPARATOR_UNNAMED, ')?',
    '(', DUE, FINAL_SEGMENT_SEPARATOR_UNNAMED, ')?',
    '(',
        '#',
        '(', SOURCE_INDICATOR, ')?',
        '(', UUID, ')?',
    ')?',  # UUID is not there for new tasks
    SPACE_UNNAMED,
    '$'    # Enforce match on the whole line
]))

DATETIME_FORMAT = "(%Y-%m-%d %H:%M)"
DATE_FORMAT = "(%Y-%m-%d)"

VIEWPORT = {
    'default':
    re.compile(
        r'^'                             # Starts at the begging of the line
        r'(?P<header_start>[=]+)'        # Heading begging
        r'(?P<name>[^=\|\[\{]*)'         # Name of the viewport, all before the | sign
                                         # Cannot include '[', '=', '|', and '{'
        r'\|'                            # Bar
        r'(?!\|)'                        # (But not two, that would be a preset)
        r'(?P<filter>[^=\|]*?)'          # Filter
        r'('                             # Optional defaults
          r'\|'                          # Bar
          r'(?P<defaults>[^=\|]+?)'      # Default attrs
        r')?'
        r'\s*'                           # Any whitespace
        r'(#(?P<source>[A-Z]))?'         # Optional source indicator
        r'\s*'                           # Any whitespace
        r'(\$(?P<sort>[A-Z]))?'          # Optional sort indicator
        r'\s*'                           # Any whitespace
        r'(limit:(?P<count>[0-9]+))?'    # Optional count indicator
        r'\s*'                           # Any whitespace
        r'[=]+'                          # Header ending
    ),
    'markdown':
    re.compile(
        r'^'                             # Starts at the begging of the line
        r'(?P<header_start>[#]+)'        # Heading begging
        r'(?P<name>[^#\|\[\{]*)'         # Name of the viewport, all before the | sign
                                         # Cannot include '[', '#', '|', and '{'
        r'\|'                            # Bar
        r'(?!\|)'                        # (But not two, that would be a preset)
        r'(?P<filter>[^#\|]*?)'          # Filter
        r'('                             # Optional defaults
          r'\|'                          # Bar
          r'(?P<defaults>[^#\|]+?)'      # Default attrs
        r')?'
        r'\s*'                           # Any whitespace
        r'(#(?P<source>[A-Z]))?'         # Optional source indicator
        r'\s*'                           # Any whitespace
        r'(\$(?P<sort>[A-Z]))?'          # Optional sort indicator
        r'\s*'                           # Any whitespace
        r'(limit:(?P<count>[0-9]+))?'    # Optional count indicator
        r'\s*'                           # Any whitespace
        r'$'                             # End of line
    )
}

HEADER = {
    'default':
    re.compile(
        r'^'                         # Starts at the beginning of the line
        r'(?P<header_start>[=]+)'    # With a positive number of =
        r'(?P<name>[^=]+)'           # Character other than =
        r'[=]+'                      # Positive number of =, closing the header
        r'\s*'                       # Allow trailing whitespace
    ),
    'markdown':
    re.compile(
        r'^'                         # Starts at the beginning of the line
        r'(?P<header_start>[#]+)'    # With a positive number of #
        r'(?P<name>[^#]+)'           # Character other than #
    )
}

PRESET = {
    'default':
    re.compile(
        r'^'                         # Starts at the beginning of the line
        r'(?P<header_start>[=]+)'    # With a positive number of =
        r'(?P<name>[^=\|\[\{]*)'     # Heading caption, everything up to ||
                                     # Cannot include '[', '=', '|, and '{'
        r'\|\|'                      # Delimiter
        r'(?P<filter>[^=\|]+?)'      # Filter preset
        r'('                         # Optional defaults
        r'\|\|'                      # Delimiter
        r'(?P<defaults>[^=\|]+?)'    # Default attrs preset
        r')?'
        r'\s*'                       # Any whitespace
        r'[=]+'                      # Header ending
    ),
    'markdown':
    re.compile(
        r'^'                         # Starts at the beginning of the line
        r'(?P<header_start>[#]+)'    # With a positive number of #
        r'(?P<name>[^#\|\[\{]*)'     # Heading caption, everything up to ||
                                     # Cannot include '[', '#', '|, and '{'
        r'\|\|'                      # Delimiter
        r'(?P<filter>[^#\|]+?)'      # Filter preset
        r'('                         # Optional defaults
        r'\|\|'                      # Delimiter
        r'(?P<defaults>[^#\|]+?)'    # Default attrs preset
        r')?'
        r'\s*'                       # Any whitespace
        r'$'                         # End of line
    )
}

ANSI_ESCAPE_SEQ = re.compile(
    r'\x1b'      # literal ESC
    r'\['        # literal [
    r'[;\d]*'    # zero or more digits or semicolons
    r'[A-Za-z]'  # a letter
    )
