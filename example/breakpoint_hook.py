# Add commands to the last breakpoint
# (gdb) comm
# info locals
# info args
# end
# (gdb) c

# Do the same with python script
# (gdb) so breakpoint_hook.py

# Before
import gdb


last_breakpoint_num = gdb.breakpoints()[-1].number

def commands(event):
    if isinstance(event, gdb.SignalEvent):
        return
    if last_breakpoint_num in (bp.number for bp in event.breakpoints):
        gdb.execute('info locals')
        gdb.execute('info args')

gdb.events.stop.connect(commands)

# After
import gdb_utils

def info_all():
    gdb.execute('info locals')
    gdb.execute('info args')

gdb_utils.commands(info_all)
# Or
gdb_utils.stop(info_all, gdb.breakpoints()[-1])
