"""This module wraps gdb and offers API with the same name of gdb commands."""
from collections import defaultdict
import re
import sys
import gdb

__all__ = [
    'br',
    'clear',
    'commands',
    'define',
    'delete',
    'disable',
    'enable',
    'info',
    'thread',
    'thread_name',
    'watch',
    'get_breakpoint',
    'globval',
    'ty']


# GDB commands
def br(location, threadnum='', condition='', commands=None,
        temporary=False, probe_modifier=''):
    """Return a gdb.Breakpoint object
    br('main.cpp:2') # break main.cpp:2
    # break 2 thread 2 if result != NULL
    br('2', threadnum=2, condition='result != NULL')
    # threadnum can be the name of specific thread.
    # We only set breakpoint on single thread, so make sure this name is unique.
    br('2', threadnum='foo')

    # break 2 and run the given function `callback`
    br('2', commands=callback)

    # temporary break
    br('2', temporary=True)
    """
    if commands is not None:
        if not hasattr(commands, '__call__'):
            raise TypeError('commands argument should be a function')
    if threadnum != '':
        if isinstance(threadnum, str):
            thread_name = find_first_threadnum_with_name(threadnum)
            if thread_name is None:
                raise gdb.GdbError('Given thread name is not found')
        threadnum = 'thread %d' % threadnum
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

def clear(*args):
    "clear('main.cpp:11')"
    gdb.execute('clear %s' % args_to_string(*args))

def commands(callback, breakpoint_num=None):
    if breakpoint_num is None:
        breakpoint_num = get_last_breakpoint().number
    register_callback_to_breakpoint_num(breakpoint_num, callback)


_define_template = """\
import gdb
class {classname}(gdb.Command):
    \"\"\"{docstring}\"\"\"
    def __init__(self):
        super(self.__class__, self).__init__("{cmdname}", gdb.COMMAND_USER)

    @classmethod
    def cmd(argv, from_tty):
        raise NotImplementError()

    def invoke(self, args, from_tty):
        argv = gdb.string_to_argv(args)
        {classname}.cmd(argv, from_tty)
{classname}()
"""
def define(cmd):
    """
    Define an user command with given function. We will forward two arguments
    to this function, first is argv(list of parameters), second is `from_tty`.

    # move.py
    def move(argv, tty):
        "Move a breakpoint to other location."
        if len(argv) != 2:
            raise gdb.GdbError('Expect two arguments, %d given' % len(argv))
        gdb.execute('delete ' + argv[0])
        gdb.execute('break ' + argv[1])
    define(move)

    (gdb) so move.py
    (gdb) help move
    Move a breakpoint to other location.
    (gdb) move 100 main.cpp:22
    """
    cmdname = cmd.__name__
    classname = cmdname.upper()
    # Use the same technic as namedtuple
    class_definition = _define_template.format(
        cmdname = cmdname,
        docstring = cmd.__doc__ if cmd.__doc__ is not None else '',
        classname = classname
    )
    namespace = dict(__name__='define_%s' % cmdname)
    exec(class_definition, namespace)
    result = namespace[classname]
    result.cmd = cmd
    result._source = class_definition
    try:
        result.__module__ = sys._getframe(1).f_globals.get(
            '__name__', '__main__')
    except (AttributeError, ValueError):
        pass
    return result


def delete(*args):
    """
    delete()              # delete all breakpoints
    delete('1')           # delete breakpoint 1
    delete('bookmark', 1) # delete bookmark 1
    delete(gdb.Breakpoint) # delete given Breakpoint object
    """
    if len(args) == 0:
        gdb.execute('delete')
    elif isinstance(args[0], gdb.Breakpoint):
        args[0].delete()
    else:
        gdb.execute('delete ' + args_to_string(*filter(None, args)))

def disable(*args):
    gdb.execute('disable ' + args_to_string(*args))

def enable(*args):
    gdb.execute('enable ' + args_to_string(*args))

def info(entry, *args):
    """In most cases, simply execute given arguments
    and return results as string.
    When `entry` is:
    * locals/args: Return dict{variable=value}
    * breakpoints: Return a list of gdb.Breakpoint
    * threads: Return a list of (is_current_thread, num, ptid, name, frame)
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
    elif entry.startswith('th'):
        return info_threads(*args)
    return gdb.execute(
        'info %s %s' % (entry, args_to_string(*args)), to_string=True)

def thread(*args):
    """
    thread(1) # switch to thread 1
    # switch to the thread which has name a.out and with the highest id
    thread('a.out')
    """
    if isinstance(args[0], str) and args[0] not in ('apply', 'find', 'name'):
        threadnum = find_first_threadnum_with_name(args[0])
        if threadnum is not None:
            gdb.execute('thread %d' % threadnum)
    else:
        gdb.execute('thread %s' % args_to_string(*args))

def thread_name(name, threadnum=None):
    """Set name to thread `threadnum`.
    If threadnum is not given, set name to current thread.
    For example: threadnum('foo', 2) will set thread 2's name to 'foo'."""
    if threadnum is not None:
        threads = info_threads()
        for th in threads:
            if th[1] == threadnum:
                original_thread_num = gdb.selected_thread().num
                gdb.execute('thread %d' % th[1], to_string=True)
                current_thread = gdb.selected_thread()
                current_thread.name = name
                gdb.execute('thread %d' % original_thread_num, to_string=True)
    else:
        gdb.execute('thread name %s' % name)

def watch(expression, condition='', commands=None):
    if commands is not None:
        if not hasattr(commands, '__call__'):
            raise TypeError('commands argument should be a function')
    if condition != '':
        condition = 'if ' + condition
    gdb.execute('watch %s %s' % (expression, condition))
    if commands is not None:
        bp = get_last_breakpoint()
        register_callback_to_breakpoint_num(bp.number, commands)
        return bp
    return get_last_breakpoint()


# Other API
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

TYPE_CACHE = {}
def ty(typename):
    """Return a gdb.Type object represents given `typename`.
    For example, x.cast(ty('Buffer'))"""
    if typename in TYPE_CACHE:
        return TYPE_CACHE[typename]

    m = re.match(r"^(\S*)\s*\*$", typename)
    if m is None:
        tp = gdb.lookup_type(typename)
    else:
        tp = gdb.lookup_type(m.group(1)).pointer()
    TYPE_CACHE[typename] = tp
    return tp

def globval(var):
    """Get global `var`'s value'"""
    return gdb.lookup_global_symbol(var).value()

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

def info_threads(*args):
    info = gdb.execute('info threads %s' % args_to_string(*args),
            to_string=True).splitlines()
    if len(info) == 1 and info[0].startswith('No '):
        return []
    group = []
    for line in info[1:]:
        is_current_thread = line[0] == '*'
        ids, _, others = line[2:].partition('"')
        idlist = ids.split()
        num = int(idlist[0])
        ptid = " ".join(idlist[1:]).strip()
        name, _, frame = others.partition('"')
        group.append((is_current_thread, num, ptid, name, frame.strip()))
    return group

def find_first_threadnum_with_name(name):
    threads = info_threads()
    for th in threads:
        if th[3] == name:
            return th[1]
    return None
