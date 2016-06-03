# (gdb) info args
# i = 2
# j = 97 'a'
# (gdb) info locals
# k = 0
# l = 108 'l'
# (gdb) info breakpoints
# Num     Type           Disp Enb Address            What
# 1       breakpoint     keep y   0x0000000000400505 in func at gdb.c:9
#         breakpoint already hit 1 time
# (gdb) so info.py
# i is 2
# k is 0
# breakpoint 1 type: 1 enable: True temp: False
# Where: gdb.c:9
import os


def print_breakpoint(bp):
    print("breakpoint %d type: %s enable: %s temp: %s" % (
        bp.number, bp.type, bp.enabled, bp.temporary))

    if bp.location is None:
        what = bp.expression
    else:
        what = os.path.relpath(bp.location, os.getcwd())
    print("Where: " + what)

    if bp.condition is not None:
        print("When: " + bp.condition)

# Before
import gdb

def convert_variable_info(text):
    group = {}
    for line in text.splitlines():
        variable, _, value = line.partition('=')
        group[variable.rstrip()] = value.lstrip()
    return group

args = convert_variable_info(gdb.execute('info args', to_string=True))
locals = convert_variable_info(gdb.execute('info locals', to_string=True))
breakpoints = gdb.breakpoints()
print('i is %s' % args['i'])
print('k is %s' % locals['k'])
print_breakpoint(breakpoints[0])

# After
import gdb_utils

args = gdb_utils.info('args')
locals = gdb_utils.info('locals')
bps = gdb_utils.info('br')
print('i is %s' % args['i'])
print('k is %s' % locals['k'])
print_breakpoint(breakpoints[0])
