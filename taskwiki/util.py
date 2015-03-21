# Various utility functions
import vim  # pylint: disable=F0401

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

        if process_next_part:
            output.append(current_part)
            current_part = ''

    if current_part:
        output.append(current_part)

    return output

def tw_modstring_to_kwargs(line):
    output = dict()
    escape_global_chars = ('"', "'")
    line = line.strip()

    args = tw_modstring_to_args(line)

    for arg in args:
        # If the argument contains :, then it's a key/value pair
        if ':' in arg:
            key, value = arg.split(':', 1)
            output[key] = value
        # Tag addition
        elif arg.startswith('+'):
            value = arg[1:]
            output.setdefault('tags', []).append(value)

    return output

def get_input(prompt="Enter: "):
    value = vim.eval('input("%s")' % prompt)
    vim.command('redraw')
    return value

def get_absolute_filepath():
    return vim.eval('expand("%:p")')

def get_current_line_number():
    row, column = vim.current.window.cursor
    return row - 1

def selected_line_numbers():
    return range(vim.current.range.start, vim.current.range.end + 1)

def show_in_split(lines, size=None, position="belowright", vertical=False,
                  name="taskwiki"):
    # Compute the size of the split
    if size is None:
        if vertical:
            # Maximum number of columns used + small offset
            size = max([len(l) for l in lines]) + 5
        else:
            # Number of lines
            size = len(lines)

    # Call 'vsplit' for vertical, otherwise 'split'
    vertical_prefix = 'v' if vertical else ''

    vim.command("{0} {1}{2}split".format(position, size, vertical_prefix))
    vim.command("edit {0}".format(name))
    vim.command("setlocal noswapfile")
    vim.command("setlocal modifiable")
    vim.current.buffer.append(lines, 0)

    vim.command("setlocal readonly")
    vim.command("setlocal nomodifiable")
    vim.command("setlocal buftype=nofile")
    vim.command("setlocal nowrap")
    vim.command("setlocal filetype=taskinfo")

    # Make the split easily closable
    vim.command("nnoremap <silent> <buffer> q :bd<CR>")
    vim.command("nnoremap <silent> <buffer> <enter> :bd<CR>")
