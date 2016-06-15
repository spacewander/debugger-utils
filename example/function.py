# typedef struct {
#   void *data;
#   unsigned int size;
# } Array;
# (gdb) so function.py
# (gdb) show convenience
# $dataType = <internal function dataType>
#
# (gdb) help function
# function dataType -- Print data according to type
#
# (gdb) p $dataType(array, 'char')
# $1 = "{ 65 'A' 66 'B' 67 'C' 68 'D' 69 'E' 70 'F' 71 'G' 72 'H' 73 'I' 74 'J'}"
# (gdb) p $dataType(array, "short")
# $2 = "{ 16961 17475 17989 18503 19017 0 0 0 0 0}"
# Before
import gdb


class DataType(gdb.Function):
    'Print data according to type'
    def __init__(self):
        super(self.__class__, self).__init__('dataType')

    def invoke(self, target, typename):
        pointer = target['data'].cast(gdb.lookup_type(typename.string()).pointer())
        data = []
        for i in range(int(target['size'])):
            elem = pointer.dereference()
            data.append(str(elem))
            pointer = pointer + 1
        return '{ ' + ' '.join(data) + '}'

DataType()

# After
import gdb_utils


def dataType(target, typename):
    'Print data according to type'
    pointer = target['data'].cast(gdb.lookup_type(typename.string()).pointer())
    data = []
    for i in range(int(target['size'])):
        elem = pointer.dereference()
        data.append(str(elem))
        pointer = pointer + 1
    return '{ ' + ' '.join(data) + '}'

gdb_utils.function(dataType)
