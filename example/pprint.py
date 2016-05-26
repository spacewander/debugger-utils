# typedef struct {
#   int *data;
#   unsigned int used;
#   unsigned int free;
# } Buffer;
# (gdb) so pprint.py
# (gdb) p buf
# $2 = used: 10
# free: 0
#  = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
# Before
import gdb


class BufferPrinter:
    """Print Buffer"""
    def __init__(self, val):
        self.val = val

    def _iterate(self, pointer, size):
        for i in range(size):
            elem = pointer.dereference()
            pointer = pointer + 1
            yield ('[%d]' % i, elem)

    def children(self):
        """Iterate children member"""
        return self._iterate(self.val['data'], int(self.val['used']))

    def to_string(self):
        """The main display data"""
        return "used: %d\nfree: %d\n" % (self.val['used'], self.val['free'])

    def display_hint(self):
        """Print like an array"""
        return 'array'


def lookup_buffer(val):
    if str(val.type) == 'Buffer':
        return BufferPrinter(val)
    return None

gdb.pretty_printers.append(lookup_buffer)


# Or register pretty printer with special shared library
def build_pretty_printerr():
    pp = gdb.printing.RegexpCollectionPrettyPrinter("Your_lib")
    pp.add_printer('Buffer', '^Buffer$', BufferPrinter)
    return pp

gdb.printing.register_pretty_printer(gdb.current_objfile(),
        build_pretty_printerr())


# After
