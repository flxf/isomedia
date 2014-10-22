import struct

ISOM_BOXES = [
    'ftyp',
]

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

def interpret_int64(data, offset=0):
    return interpret_int(data, offset, 64)

def interpret_int32(data, offset=0):
    return interpret_int(data, offset, 32)

def interpret_int16(data, offset=0):
    return interpret_int(data, offset, 16)

def interpret_int8(data, offset=0):
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

    def __init__(self, data, document, parent_atom, file_offset):
        atom_type, atom_size, _ = interpret_atom_header(data)
        self._type = atom_type
        self._size = atom_size

        self.document = document
        self._data = data
        self.parent_atom = parent_atom

        self._input_file_offset = file_offset
        self._input_size = interpret_atom_header(self._data)[1]

    def __repr__(self):
        return str({
            'type': self.type()
        })

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        assert isinstance(value, str), 'A box\'s type field should be a string.'
        assert len(value) == 4, 'A box\'s type should be 4 bytes exactly.'
        self._type = value

    def size(self):
        return interpret_atom_header(self._data)[1]

    def get_data(self):
        if len(self._data) != self.size():
            raise NotImplementedError
        return self._data

class FullAtom(Atom):
    def version(self):
        return interpret_int8(self._data, offset=9)

    def flags(self):
        return self._data[10:13]

class ContainerAtom(Atom):
    def __init__(self, data, document, parent_atom, file_offset):
        Atom.__init__(self, data, document, parent_atom, file_offset)
        self.children = []

    def __repr__(self):
        return str({
            'type': self.type(),
            'children': self.children
        })

    def append_child(self, child):
        self.size += child.size
        self.children.append(child)

# ISOM Defined Boxes
class LazyLoadAtom(Atom):
    LOAD_DATA = False

    def get_data(self):
        if self._data is None:
            fp = self.document.fp
            fp.seek(self._input_file_offset)
            self._data = fp.read(self._input_size)

        return self._data

class FreeAtom(LazyLoadAtom):
    pass

class SkipAtom(LazyLoadAtom):
    pass

class MdatAtom(LazyLoadAtom):
    pass

class UserExtendedAtom(Atom):
    # TODO: How should I surface both uuid and the extended types
    def type(self):
        header_length = interpret_atom_header(self._data)[2]
        return self._data[header_length:header_length+16]

class FtypAtom(Atom):
    def major_brand(self):
        header_length = interpret_atom_header(self._data)[2]
        return self._data[header_length:header_length+4]

ATOM_TYPE_TO_CLASS = {
    'free': FreeAtom,
    'ftyp': FtypAtom,
    'mdat': MdatAtom,
    'skip': SkipAtom,
    'uuid': UserExtendedAtom,
}
