# Various utility functions
from __future__ import print_function
from distutils.version import LooseVersion

import contextlib
import pkg_resources
import os
import regexp
import random
import sys
import vim  # pylint: disable=F0401

from errors import TaskWikiException

# Detect if command AnsiEsc is available
ANSI_ESC_AVAILABLE = vim.eval('exists(":AnsiEsc")') == '2'


def tw_modstring_to_args(line):
    output = []
    escape_global_chars = ('"', "'")
    line = line.strip()

    current_escape = None
    current_part = ''
    local_escape_pos = None

    for i in range(len(line)):
        char = line[i]
        ignored = False
        process_next_part = False

        # If previous char was \, add to current part no matter what
        if local_escape_pos == i - 1:
            local_escape_pos = None
        # If current char is \, use it as escape mark and ignore it
        elif char == '\\':
            local_escape_pos = i
            ignored = True
        # If current char is ' or ", open or close an escaped seq
        elif char in escape_global_chars:
            # First test if we're finishing an escaped sequence
            if current_escape == char:
                current_escape = None
                ignored = True
            # Do we have ' inside "" or " inside ''?
            elif current_escape is not None:
                pass
            # Opening ' or "
            else:
                current_escape = char
                ignored = True
        elif current_escape is not None:
            pass
        elif char == ' ':
            ignored = True
            process_next_part = True

        if not ignored:
            current_part += char

        if process_next_part and current_part:
            output.append(current_part)
            current_part = ''

    if current_part:
        output.append(current_part)

    return output

def tw_modstring_to_kwargs(line):
    args = tw_modstring_to_args(line)
    return tw_args_to_kwargs(args)

def tw_args_to_kwargs(args):
    output = dict()
    meta = dict()  # Store meta attributes

    for arg in args:
        # If the argument contains :, then it's a key/value pair
        if ':' in arg:
            key, value = arg.split(':', 1)
            # Ignore anything which is not one-word string of alpha chars
            # This will skip over constructs with attribute modifiers
            if key.isalpha():
                output[key] = value if value is not "" else None
        # Tag addition
        elif arg.startswith('+'):
            value = arg[1:]
            # Ignore virtual tags
            if not value.isupper():
                output.setdefault('tags', []).append(value)
            # Ignore tag removal

    return output

def get_input(prompt="Enter: ", allow_empty=False):
    value = vim.eval('input("%s")' % prompt)
    vim.command('redraw')

    # Check for empty value and bail out if not allowed
    if not value and not allow_empty:
        raise TaskWikiException("Input must be provided.")

    return value

def get_current_window():
    """
    Returns a current window number. Provides a workaround for Neovim.
    """

    try:
        return vim.current.window.number - 1
    except AttributeError:
        return int(vim.eval('winnr()')) - 1

def convert_colorstring_for_vim(string):
    BASIC_COLORS = [
        "blue", "yellow", "green", "red",
        "magneta", "yellow", "white", "black"
        ]

    EFFECTS = ['bold']

    def is_color(c):
        return any([
            c.startswith('color'),
            c.startswith('rgb'),
            c in BASIC_COLORS
        ])

    def parse_color(c):
        if c.startswith('color'):
            return c[5:]
        elif c.startswith('rgb'):
            # TaskWarrior color cube notation, see 'task color'
            red = int(c[3])
            green = int(c[4])
            blue = int(c[5])
            index = 16 + red * 36 + green * 6 + blue;
            return str(index)
        else:
            return c

    foreground = None
    background = None
    effect = None

    for part in string.split():
        if is_color(part) and foreground is None:
            foreground = parse_color(part)
        elif is_color(part) and background is None:
            background = parse_color(part)
        elif part in EFFECTS:
            effect = part

    result = ''.join([
        'cterm={0} '.format(effect) if effect else '',
        'ctermfg={0} '.format(foreground) if foreground else '',
        'ctermbg={0}'.format(background) if background else '',
        ])

    return result

def get_buffer_shortname():
    return vim.eval('expand("%")')

def get_absolute_filepath():
    return vim.eval('expand("%:p")')

def get_current_line_number():
    row, column = vim.current.window.cursor
    return row - 1

def get_valid_tabpage_buffers(tabpage):
    return [win.buffer for win in tabpage.windows if win.buffer.valid]

def buffer_shortname(buffer):
    return os.path.basename(buffer.name)

def selected_line_numbers():
    return range(vim.current.range.start, vim.current.range.end + 1)

def get_lines_above(including_current=True):
    # Add 1 to the current line number if we want to include this line
    bonus = 1 if including_current else 0

    for line in reversed(range(0, get_current_line_number() + bonus)):
        yield vim.current.buffer[line]

def strip_ansi_escape_sequence(string):
    return regexp.ANSI_ESCAPE_SEQ.sub("", string)

def show_in_split(lines, size=None, position="belowright", vertical=False,
                  name="taskwiki", replace_opened=True,
                  activate_cursorline=False):

    # If there is no output, bail
    if not lines:
        print("No output.", file=sys.stderr)
        return

    # Sanitaze the output
    lines = [l.rstrip() for l in lines]

    # If the multiple buffers with this name are not desired
    # cloase all the old ones in this tabpage
    if replace_opened:
        for buf in get_valid_tabpage_buffers(vim.current.tabpage):
            shortname = buffer_shortname(buf)
            if shortname.startswith(name):
                vim.command('bwipe {0}'.format(shortname))

    # Generate a random suffix for the buffer name
    # This is needed since AnsiEsc saves the buffer name inside
    # s: scoped variables. Also lowers the probability of clash with
    # a real file.
    random_suffix = random.randint(1,100000)
    name = '{0}.{1}'.format(name, random_suffix)

    # Compute the size of the split
    if size is None:
        if vertical:
            # Maximum number of columns used + small offset
            # Strip the color codes, since they do not show up in the split
            size = max([len(strip_ansi_escape_sequence(l)) for l in lines]) + 1

            # If absolute maximum width was set, do not exceed it
            if vim.vars.get('taskwiki_split_max_width'):
                size = min(size, vim.vars.get('taskwiki_split_max_width'))

        else:
            # Number of lines
            size = len(lines)

            # If absolute maximum height was set, do not exceed it
            if vim.vars.get('taskwiki_split_max_height'):
                size = min(size, vim.vars.get('taskwiki_split_max_height'))

    # Set cursorline in the window
    cursorline_activated_in_window = None

    if activate_cursorline and not vim.current.window.options['cursorline']:
        vim.current.window.options['cursorline'] = True
        cursorline_activated_in_window = get_current_window()

    # Call 'vsplit' for vertical, otherwise 'split'
    vertical_prefix = 'v' if vertical else ''

    vim.command("{0} {1}{2}split".format(position, size, vertical_prefix))
    vim.command("edit {0}".format(name))

    # For some weird reason, edit does not work for some users, but
    # enew + file <name> does. Use as fallback.
    if get_buffer_shortname() != name:
        vim.command("enew")
        vim.command("file {0}".format(name))

    # If we were still unable to open the buffer, bail out
    if get_buffer_shortname() != name:
        print("Unable to open a new buffer with name: {0}".format(name))
        return

    # We're good to go!
    vim.command("setlocal noswapfile")
    vim.command("setlocal modifiable")
    vim.current.buffer.append(lines, 0)

    vim.command("setlocal readonly")
    vim.command("setlocal nomodifiable")
    vim.command("setlocal buftype=nofile")
    vim.command("setlocal nowrap")
    vim.command("setlocal nonumber")

    # Keep window size fixed despite resizing
    vim.command("setlocal winfixheight")
    vim.command("setlocal winfixwidth")

    # Make the split easily closable
    vim.command("nnoremap <silent> <buffer> q :bwipe<CR>")
    vim.command("nnoremap <silent> <buffer> <enter> :bwipe<CR>")

    # Remove cursorline in original window if it was this split which set it
    if cursorline_activated_in_window is not None:
        vim.command("au BufLeave,BufDelete,BufWipeout <buffer> "
                    ":py vim.windows[{0}].options['cursorline']=False"
                    .format(cursorline_activated_in_window))

    if ANSI_ESC_AVAILABLE:
        vim.command("AnsiEsc")

def tw_execute_colorful(tw, *args, **kwargs):
    override = kwargs.setdefault('config_override', {})
    maxwidth = kwargs.pop('maxwidth', False)
    maxheight = kwargs.pop('maxheight', False)

    if ANSI_ESC_AVAILABLE:
        override['_forcecolor'] = "yes"

    if maxheight:
        override['defaultheight'] = vim.current.window.height

    if maxwidth:
        override['defaultwidth'] = vim.current.window.width

    return tw_execute_safely(tw, *args, **kwargs)

def tw_execute_safely(tw, *args, **kwargs):
    kwargs['allow_failure'] = False
    kwargs['return_all'] = True

    out, err, rc = tw.execute_command(*args, **kwargs)

    if rc == 0:
        return out
    else:
        # In case of failure, print everything as os output
        # Left for debug mode
        # for line in itertools.chain(out, err[:-1]):
        #    print(line)
        # Display the last line as failure
        if err:
            print(err[-1], file=sys.stderr)

@contextlib.contextmanager
def current_line_highlighted():
    original_value = vim.current.window.options['cursorline']
    original_window_number = get_current_window()
    vim.current.window.options['cursorline'] = True

    vim.command('redraw')

    try:
        yield
    finally:
        original_window = vim.windows[original_window_number]
        original_window.options['cursorline'] = original_value

def enforce_dependencies(cache):
    # Vim version is already checked in vimscript file
    # This is done so that we avoid problems with +python

    TASKLIB_VERSION = '0.10.0'
    TASKWARRIOR_VERSION = '2.4.0'

    # Check tasklib version
    tasklib_module_info = pkg_resources.get_distribution('tasklib')
    tasklib_installed_version = LooseVersion(tasklib_module_info.version)
    tasklib_required_version = LooseVersion(TASKLIB_VERSION)

    if tasklib_required_version > tasklib_installed_version:
        raise TaskWikiException("Tasklib version at least %s is required."
                                % TASKLIB_VERSION)

    # Check taskwarrior version
    tw = cache.warriors['default']
    taskwarrior_installed_version = LooseVersion(tw.version)
    taskwarrior_required_version = LooseVersion(TASKWARRIOR_VERSION)

    if taskwarrior_required_version > taskwarrior_installed_version:
        raise TaskWikiException("Taskwarrior version at least %s is required."
                                % TASKWARRIOR_VERSION)
