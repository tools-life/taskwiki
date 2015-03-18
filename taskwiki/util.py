# Various utility functions

def parse_tw_arg_string(line):
    output = dict()
    escape_global_chars = ('"', "'")
    line = line.strip()

    current_escape = None
    current_part = ''
    current_key = ''
    current_value = ''
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
        elif char == ':':
            ignored = True
            process_next_part = True

        if not ignored:
            current_part += char

        if process_next_part:
            if current_key:
                current_value = current_part
                output[current_key] = current_value
                current_part = ''
                current_key = ''
                current_value = ''
            else:
                current_key = current_part
                current_part = ''

    current_value = current_part
    output[current_key] = current_value

    return output
