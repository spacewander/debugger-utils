# Utilities for extending gdb with python

## Usage

1. Download `debugger-utils` to directory `X`
2. Put these to your `~/.gdbinit`:
```
python import sys; sys.path.append('$X/debugger-utils')
```
`$X` is where `debugger-utils` lies in.
3. `import gdb_utils` in your python script.

## Example

```python
# Create a gdb commands in hello.py
import gdb_utils


def hello(who, *args):
    """
    Say hello.
    """
    print('hello %s', who)
gdb_utils.define(hello)
#(gdb) so hello.py
#(gdb) hello 'world'
```

For more examples, see [example](./example).

## API

GDB commands:

- [x] break
- [x] clear
- [x] commands
- [x] delete
- [x] disable
- [x] define
- [x] enable
- [x] info
- [x] thread
- [x] thread_name
- [x] watch

Other API:

- [x] get_breakpoint
- [x] function
- [x] stop
- [x] register_pprinter
- [x] build_pprinter
- [x] globval
- [x] ty

For more info, see [API.md](./API.md).
