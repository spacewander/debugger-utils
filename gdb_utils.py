"""This module wraps gdb and offers API with the same name of gdb commands."""
from collections import defaultdict
import gdb

__all__ = ['get_breakpoint', 'br', 'delete', 'info']


def get_breakpoint(location=None, expression=None, condition=None, number=None):
    """Return last breakpoint if not arguments given,
    or the breakpoint with given number if `number` given,
    or the first breakpoint matched given 
    `location`(for `breakpoint`)/`expression`(for watchpoint) and `condtion`.

    If there is no any breakpoint,
    raise gdb.GdbError('No breakpoints or watchpoints.')
    If there is no matched breakpoint, return None.
    """
    if location is None and expression is None and number is None:
        return get_last_breakpoint()
    bps = gdb.breakpoints()
    if bps is None: raise gdb.GdbError('No breakpoints or watchpoints.')

    if number is not None:
        for bp in bps:
            if bp.number == number:
                return bp
    else:
        for bp in bps:
            if (bp.location == location and bp.expression == expression and
                bp.condition == condition):
                return bp
    return None

def br(location, threadnum='', condition='', commands=None,
        temporary=False, probe_modifier=''):
    """Return a gdb.Breakpoint object
    br('main.cpp:2') # break main.cpp:2
    # break 2 thread 2 if result != NULL
    br('2', threadnum=2, condition='result != NULL')

    # break 2 and run the given function `callback`
    br('2', commands=callback)

    # temporary break
    br('2', temporary=True)
    """
    if commands is not None:
        if hasattr(commands, '__call__'):
            raise TypeError('commands argument should be a list or a function')
    if threadnum != '':
        threadnum = 'thread %d' % int(threadnum)
    if condition != '':
        condition = 'if ' + condition
    if temporary:
        gdb.execute('tbreak ' + args_to_string(
            probe_modifier, location, threadnum, condition))
    else:
        gdb.execute('break ' + args_to_string(
            probe_modifier, location, threadnum, condition))
    if commands is not None:
        bp = get_last_breakpoint()
        register_callback_to_breakpoint_num(bp.number, commands)
        return bp
    return get_last_breakpoint()

def delete(*args):
    """
    delete()              # delete all breakpoints
    delete('1')           # delete breakpoint 1
    delete('bookmark', 1) # delete bookmark 1
    delete(gdb.Breakpoint) # delete given Breakpoint object
    """
    if isinstance(args[0], gdb.Breakpoint):
        args[0].delete()
    else:
        gdb.execute('delete ' + args_to_string(*args))

def info(entry, *args):
    """In most cases, simply execute given arguments
    and return results as string.
    When `entry` is:
    * locals/args: Return dict{variable=value}
    * breakpoints: Return a list of gdb.Breakpoint
    """
    if entry.startswith(('ar', 'lo')):
        info = gdb.execute('info ' + entry, to_string=True).splitlines()
        # No arguments or No locals
        if len(info) == 1 and info[0].startswith('No '):
            return {}
        group = {}
        for line in info:
            variable, _, value = line.partition('=')
            group[variable.rstrip()] = value.lstrip()
        return group
    elif entry.startswith('b'):
        return gdb.breakpoints()
    return gdb.execute(
        'info %s %s' % (entry, args_to_string(*args)), to_string=True)

# Helpers
def str_except_none(arg):
    if arg is None:
        return ''
    return str(arg)

def args_to_string(*args):
    return ' '.join(map(str_except_none, args))

def get_last_breakpoint():
    bps = gdb.breakpoints()
    if bps is None: raise gdb.GdbError('No breakpoints or watchpoints.')
    return bps[-1]

STOP_EVENT_REGISTER = defaultdict(list)
def register_callback_to_breakpoint_num(breakpoint_num, callback):
    STOP_EVENT_REGISTER[breakpoint_num].append(callback)

def trigger_registered_callback(num):
    if num in STOP_EVENT_REGISTER:
        for cb in STOP_EVENT_REGISTER[num]:
            cb()

def stop_handler(event):
    for bp in event.breakpoints:
        trigger_registered_callback(bp.number)

gdb.events.stop.connect(stop_handler)
