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
    'register_pprinter',
    'stop',
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

def commands(callback, breakpoint_num=None, remove=False):
    """If `breakpoint_num` is not given, add callback to last breakpoint,
    else add to specific breakpoint.
    If`remove` is True, remove the callback instead of adding it."""
    if remove is False:
        if breakpoint_num is None:
            bp = get_last_breakpoint()
            if bp is None:
                raise gdb.GdbError('No breakpoints specified')
            breakpoint_num = bp.number
        register_callback_to_breakpoint_num(breakpoint_num, callback)
    else:
        if breakpoint_num is None:
            bp = get_last_breakpoint()
            if bp is None:
                raise gdb.GdbError('No breakpoints specified')
            breakpoint_num = bp.number
        remove_callback_to_breakpoint_num(breakpoint_num, callback)


_define_template = """\
import gdb
class {classname}(gdb.Command):
    \"\"\"{docstring}\"\"\"
    def __init__(self):
        super(self.__class__, self).__init__("{cmdname}", gdb.COMMAND_USER)

    @classmethod
    def cmd(argv, from_tty):
        raise NotImplementError('cmd')

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
    return eval_template(_define_template, cmd)


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

_function_template = """\
import gdb
class {classname}(gdb.Function):
    \"\"\"{docstring}\"\"\"
    def __init__(self):
        super(self.__class__, self).__init__("{cmdname}")

    @classmethod
    def cmd(*args):
        raise NotImplementError('func')

    def invoke(self, *args):
        return {classname}.cmd(*args)
{classname}()
"""
def function(func):
    """Define a gdb convenience function with user specific function.

    # greet.py
    def greet(name):
        "The `name` argument will be a gdb.Value"
        return "Hello, %s" % name.string()
    function(func)

    (gdb) so greet.py
    (gdb) p $greet("World")
    $1 = "Hello World"
    """
    return eval_template(_function_template, func)


def stop(callback, breakpoint=None, remove=False):
    """Run callback while gdb stops on breakpoints.
    If `breakpoint` is given, run it while specific breakpoint is hit.
    If `remove` is True, remove callback instead of adding it.
    """
    if not remove:
        if isinstance(breakpoint, gdb.Breakpoint):
            register_callback_to_breakpoint_num(breakpoint.number, callback)
        else:
            gdb.events.stop.connect(callback)
    else:
        if isinstance(breakpoint, gdb.Breakpoint):
            remove_callback_to_breakpoint_num(breakpoint.number, callback)
        else:
            gdb.events.stop.disconnect(callback)


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

def register_pprinter(pprinter, pattern):
    """Register given pprinter to class matched given pattern."""
    if not hasattr(pprinter, 'to_string'):
        raise gdb.GdbError(
                'A pretty printer should implement `to_string` method.')
    pp = (lambda val: pprinter(val)
                if re.match(pattern, str(val.type)) else None)
    # Set a name so that we can enable/disable with its name
    pp.__name__ = pprinter.__name__
    gdb.pretty_printers.append(pp)


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

STOP_EVENT_REGISTER = defaultdict(set)
def register_callback_to_breakpoint_num(breakpoint_num, callback):
    STOP_EVENT_REGISTER[breakpoint_num].add(callback)

def remove_callback_to_breakpoint_num(breakpoint_num, callback):
    if callback in STOP_EVENT_REGISTER[breakpoint_num]:
        STOP_EVENT_REGISTER[breakpoint_num].remove(callback)

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

def eval_template(template, cmd):
    cmdname = to_classname(cmd.__name__)
    classname = cmdname.upper()
    # Use the same technic as namedtuple
    class_definition = template.format(
        cmdname = cmdname,
        docstring = cmd.__doc__ if cmd.__doc__ is not None else '',
        classname = classname
    )
    namespace = dict(__name__='template_%s' % cmdname)
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


_pp_template = """\
class {classname}:
    def __init__(self, val):
        self.val = val

    @classmethod
    def _to_string(val):
        raise NotImplementError('to_string')

    def to_string(self):
        return {classname}._to_string(self.val)
"""
_display_hint_snippet = """
    def display_hint(self):
        raise NotImplementError('display_hint')
"""
_children_snippet = """
    @classmethod
    def _children(val):
        raise NotImplementError('children')

    def children(self):
        return {classname}._children(self.val)
"""
def build_pprinter(to_string, display_hint=None, children=None):
    """Build a pretty printer.
    For example:
    def buffer_pretty_printer(val):
        return "size: %d\n" % self.val['size']
    pp = build_pprinter(buffer_pretty_printer)

    ... is equal to:

    class BufferPrettyPrinter:
        def __init__(self, val):
            self.val = val
        def to_string(self):
            return "size: %d\n" % self.val['size']
    pp = BufferPrettyPrinter
    """
    classname = to_classname(to_string.__name__)
    template = _pp_template
    if display_hint is not None:
        template += _display_hint_snippet
    if children is not None:
        template += _children_snippet
    class_definition = template.format(
        classname = classname
    )
    namespace = dict(__name__='template_%s' % classname)
    exec(class_definition, namespace)
    result = namespace[classname]

    result._to_string = to_string
    if display_hint is not None:
        result.display_hint = lambda self: display_hint
    if children is not None:
        result._children = children

    result._source = class_definition
    try:
        result.__module__ = sys._getframe(1).f_globals.get(
            '__name__', '__main__')
    except (AttributeError, ValueError):
        pass
    return result

def to_classname(name):
    return ''.join(word.capitalize() for word in name.split('_'))
