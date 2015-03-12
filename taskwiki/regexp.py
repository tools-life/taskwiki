import re

# Unnamed building blocks
UUID_UNNAMED = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
DUE_UNNAMED = r'\(\d{4}-\d\d-\d\d( \d\d:\d\d)?\)'
SPACE_UNNAMED = r'\s*'
NONEMPTY_SPACE_UNNAMED = r'\s+'
FINAL_SEGMENT_SEPARATOR_UNNAMED = r'(\s+|$)'

TEXT_FORBIDDEN_SUFFIXES = (
    r'\s',  # Text cannot end with whitespace
    r' !', r' !!', r' !!!',  # Any priority value
    r'\(\d{4}-\d\d-\d\d\)', r'\(\d{4}-\d\d-\d\d \d\d:\d\d\)',  # Any datetime value
    r'\(\d{4}-\d\d-\d\d',  # Any datetime value
    UUID_UNNAMED,  # Text cannot end with UUID
)

# Building blocks
BRACKET_OPENING = re.escape('* [')
BRACKET_CLOSING = re.escape('] ')
EMPTY_SPACE = r'(?P<space>\s*)'
UUID = r'(?P<uuid>{0})'.format(UUID_UNNAMED)
DUE = r'(?P<due>{0})'.format(DUE_UNNAMED)
UUID_COMMENT = '#{0}'.format(UUID)
TEXT = r'(?P<text>.+' + ''.join(['(?<!%s)' % suffix for suffix in TEXT_FORBIDDEN_SUFFIXES]) + ')'
COMPLETION_MARK = r'(?P<completed>.)'
PRIORITY = r'(?P<priority>!{1,3})'

GENERIC_TASK = re.compile(''.join([
    EMPTY_SPACE,
    BRACKET_OPENING,
    COMPLETION_MARK,
    BRACKET_CLOSING,
    TEXT,
    FINAL_SEGMENT_SEPARATOR_UNNAMED,
    '(', PRIORITY, FINAL_SEGMENT_SEPARATOR_UNNAMED, ')?'
    '(', DUE, FINAL_SEGMENT_SEPARATOR_UNNAMED, ')?'
    '(', UUID_COMMENT, FINAL_SEGMENT_SEPARATOR_UNNAMED, ')?'  # UUID is not there for new tasks
]))

PROJECT_DEFINITION = re.compile(r'Project: (?P<project>.*)(?<!\s)')

DATETIME_FORMAT = "(%Y-%m-%d %H:%M)"
DATE_FORMAT = "(%Y-%m-%d)"

