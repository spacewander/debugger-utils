## br(location, threadnum='', condition='', commands=None, temporary=False, probe_modifier='')
```
Return a gdb.Breakpoint object
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
```

## clear()
```
clear('main.cpp:11')
```

## commands(callback, breakpoint_num=None, remove=False)
```
If `breakpoint_num` is not given, add callback to last breakpoint,
else add to specific breakpoint.
If`remove` is True, remove the callback instead of adding it.
```

## define(cmd)
```
Define an user command with given function. We will forward two arguments
to this function, first is argv(list of parameters), second is `from_tty`.

# move.py
import gdb_utils
def move(argv, tty):
    "Move a breakpoint to other location."
    if len(argv) != 2:
        raise gdb.GdbError('Expect two arguments, %d given' % len(argv))
    gdb.execute('delete ' + argv[0])
    gdb.execute('break ' + argv[1])
gdb_utils.define(move)

(gdb) so move.py
(gdb) help move
Move a breakpoint to other location.
(gdb) move 100 main.cpp:22
```

## delete()
```
delete()              # delete all breakpoints
delete('1')           # delete breakpoint 1
delete('bookmark', 1) # delete bookmark 1
delete(gdb.Breakpoint) # delete given Breakpoint object
```

## disable()
```
Similar to gdb command 'disable'.
```

## enable()
```
Similar to gdb command 'enable'.
```

## info(entry)
```
In most cases, simply execute given arguments
and return results as string.
When `entry` is:
* locals/args: Return dict{variable=value}
* breakpoints: Return a list of gdb.Breakpoint
* threads: Return a list of (is_current_thread, num, ptid, name, frame)
```

## thread()
```
thread(1) # switch to thread 1
# switch to the thread which has name a.out and with the highest id
thread('a.out')
```

## thread_name(name, threadnum=None)
```
Set name to thread `threadnum`.
If threadnum is not given, set name to current thread.
For example: threadnum('foo', 2) will set thread 2's name to 'foo'.
```

## watch(expression, condition='', commands=None)
```
# watch array.len if size > 20
watch('array.len', condition='size > 20')
```

## get_breakpoint(location=None, expression=None, condition=None, number=None)
```
Return last breakpoint if not arguments given,
or the breakpoint with given number if `number` given,
or the first breakpoint matched given
`location`(for `breakpoint`)/`expression`(for watchpoint) and `condition`.

If there is no any breakpoint,
raise gdb.GdbError('No breakpoints or watchpoints.')
If there is no matched breakpoint, return None.
```

## function(func)
```
Define a gdb convenience function with user specific function.

# greet.py
import gdb_utils
def greet(name):
    "The `name` argument will be a gdb.Value"
    return "Hello, %s" % name.string()
gdb_utils.function(func)

(gdb) so greet.py
(gdb) p $greet("World")
$1 = "Hello World"
```

## stop(callback, breakpoint=None, remove=False)
```
Run callback while gdb stops on breakpoints.
If `breakpoint` is given, run it while specific breakpoint is hit.
If `remove` is True, remove callback instead of adding it.
```

## ty(typename)
```
Return a gdb.Type object represents given `typename`.
For example, x.cast(ty('Buffer'))
```

## globval(var)
```
Get global `var`'s value
```

## register_pprinter(pprinter, pattern)
```
Register given pprinter to class matched given pattern.
```

## build_pprinter(to_string, display_hint=None, children=None)
```
Build a pretty printer.
    For example:
    def buffer_pretty_printer(val):
        return "size: %d\n" % self.val['size']
    def children(val):
        return []
    pp = build_pprinter(buffer_pretty_printer, display_hint='array',
            children=children)

    ... is equal to:

    class BufferPrettyPrinter:
        def __init__(self, val):
            self.val = val
        def to_string(self):
            return "size: %d\n" % self.val['size']
        def children(self):
            return []
        def display_hint(self):
            return 'array'
    pp = BufferPrettyPrinter

```

