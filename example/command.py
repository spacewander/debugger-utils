# (gdb) so command.py
# (gdb) help mv
# Move breakpoint.
# Usage: mv old_breakpoint_num new_breakpoint
# Example:
#   (gdb) mv 1 binary_search -- move breakpoint 1 to `b binary_search`
#
# (gdb) mv 1 binary_search

# Before
import gdb


class Move(gdb.Command):
    """Move breakpoint
    Usage: mv old_breakpoint_num new_breakpoint
    Example:
        (gdb) mv 1 binary_search -- move breakpoint 1 to `b binary_search`
    """
    def __init__(self):
        super(self.__class__, self).__init__("mv", gdb.COMMAND_USER)

    def invoke(self, args, from_tty):
        argv = gdb.string_to_argv(args)
        if len(argv) != 2:
            raise gdb.GdbError('输入参数数目不对，help mv以获得用法')
        gdb.execute('delete ' + argv[0])
        gdb.execute('break ' + argv[1])

Move()

# After
import gdb_utils

def move(argv, from_tty):
    if len(argv) != 2:
        raise gdb.GdbError('输入参数数目不对，help mv以获得用法')
    gdb_utils.delete(argv[0])
    gdb_utils.br(argv[1])

gdb_utils.define(move)
