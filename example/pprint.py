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

# After
import gdb_utils


def _iterate(pointer, size):
    for i in range(size):
        elem = pointer.dereference()
        pointer = pointer + 1
        yield ('[%d]' % i, elem)

def iter_data(val):
    return _iterate(val['data'], int(val['used']))

def to_string(val):
    return "used: %d\nfree: %d\n" % (val['used'], val['free'])

pp = gdb_utils.build_pprinter(to_string, display_hint='array',
        children=iter_data)
gdb_utils.register_pprinter(pp, pattern='^Buffer$')
