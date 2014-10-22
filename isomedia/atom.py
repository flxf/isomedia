import struct

CONTAINER_ATOMS = [
    '\xa9alb',
    '\xa9art',
    '\xa9cmt',
    '\xa9day',
    '\xa9gen',
    '\xa9grp',
    '\xa9lyr',
    '\xa9nam',
    '\xa9too',
    '\xa9wrt',
    'catg',
    'covr',
    'cpil',
    'cptr',
    'desc',
    'disk',
    'egid',
    'gnre',
    'ilst',
    'keyw',
    'moov',
    'pcst',
    'pgap',
    'purd',
    'purl',
    'rtng',
    'stik',
    'tmpo',
    'trak',
    'trkn',
    'tven',
    'tves',
    'tvnn',
    'tvsh',
    'tvsn',
    'udta',
]

BYTES_TO_UNPACK_FORMAT = {
    8: '>B',
    16: '>H',
    32: '>I',
    64: '>Q'
}

def interpret_int(data, offset, size):
    assert size in BYTES_TO_UNPACK_FORMAT
    field = data[offset:offset + (size / 8)]
    return struct.unpack(BYTES_TO_UNPACK_FORMAT[size], field)[0]

def interpret_int64(data, offset):
    return interpret_int(data, offset, 64)

def interpret_int32(data, offset):
    return interpret_int(data, offset, 32)

def interpret_int16(data, offset):
    return interpret_int(data, offset, 16)

def interpret_int8(data, offset):
    return interpret_int(data, offset, 8)

def interpret_atom_header(data):
    atom_size = interpret_int32(data, 0)
    atom_type = data[4:8]

    if atom_size == 1:
        atom_size = interpret_int64(data, 8)
        header_length = 16
    else:
        header_length = 8

    return (atom_type, atom_size, header_length)

class Atom(object):
    # Enable lazy-loading
    LOAD_DATA = True

    def __init__(self, data, parent_atom, file_offset):
        self._data = data
        self.parent_atom = parent_atom
        self._input_file_offset = file_offset

    def __repr__(self):
        return str({
            'type': self.type()
        })

    def type(self):
        return self._data[4:8]

    def size(self):
        return interpret_atom_header(self._data)[1]

    def get_data(self):
        if len(self._data) != self.size():
            raise NotImplementedError
        return self._data

class ContainerAtom(Atom):
    def __init__(self, data, parent_atom, file_offset):
        Atom.__init__(self, data, parent_atom, file_offset)
        self.children = []

    def __repr__(self):
        return str({
            'type': self.type(),
            'children': self.children
        })

class RootAtom(ContainerAtom):
    # This is a fictional atom

    def __init__(self):
        ContainerAtom.__init__(self, None, None, 0)

    def type(self):
        return 'root-fakeatom'

class MdatAtom(Atom):
    LOAD_DATA = False

ATOM_TYPE_TO_CLASS = {
    'mdat': MdatAtom
}
