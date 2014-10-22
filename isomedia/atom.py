from itertools import chain
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

UINT_BYTES_TO_FORMAT = {
    8: '>B',
    16: '>H',
    32: '>I',
    64: '>Q'
}

MAX_UINT32 = (2 ** 32) - 1

def interpret_int(data, offset, size):
    assert size in UINT_BYTES_TO_FORMAT
    field = data[offset:offset + (size / 8)]
    return struct.unpack(UINT_BYTES_TO_FORMAT[size], field)[0]

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

def write_atom_header(atom):
    header = ''

    if atom.size >= MAX_UINT32:
        header += struct.pack(UINT_BYTES_TO_FORMAT[32], 1)
    else:
        header += struct.pack(UINT_BYTES_TO_FORMAT[32], atom.size)
    header += atom.type
    if atom.size >= MAX_UINT32:
        header += struct.pack(UINT_BYTES_TO_FORMAT[64], atom.size)

    return header

class Atom(object):
    # Enable lazy-loading
    LOAD_DATA = True

    def __init__(self, data, document, parent_atom, file_offset):
        atom_type, atom_size, header_length = interpret_atom_header(data)
        self._type = atom_type
        self.size = atom_size
        self._body_offset = header_length

        self.document = document
        self.parent_atom = parent_atom

        self._input_file_offset = file_offset
        self._input_size = atom_size

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

    def to_bytes(self):
        raise NotImplementedError

class FullAtom(Atom):
    def __init__(self, data, document, parent_atom, file_offset):
        Atom.__init__(self, data, document, parent_atom, file_offset)

        # Can a full-box have an extended header?
        self.version = interpret_int8(data, offset=9)
        self.flags = data[10:13]

class ContainerAtom(Atom):
    def __init__(self, data, document, parent_atom, file_offset):
        Atom.__init__(self, data, document, parent_atom, file_offset)
        self.children = []

    def __repr__(self):
        return str({
            'type': self.type(),
            'children': self.children
        })

    def to_bytes(self):
        header_bytes = write_atom_header(self)
        return ''.join(chain(header_bytes, (child.to_bytes() for child in self.children)))

    def append_child(self, child):
        self.size += child.size
        self.children.append(child)

class GenericAtom(Atom):
    def __init__(self, data, document, parent_atom, file_offset):
        Atom.__init__(self, data, document, parent_atom, file_offset)
        self._data = data

    def get_data(self):
        return self._data

    def to_bytes(self):
        return self.get_data()

class LazyLoadAtom(Atom):
    LOAD_DATA = False

    def __init__(self, data, document, parent_atom, file_offset):
        Atom.__init__(self, data, document, parent_atom, file_offset)
        self._data = None

    def get_data(self):
        if self._data is None:
            fp = self.document.fp
            fp.seek(self._input_file_offset)
            self._data = fp.read(self._input_size)

        return self._data

    def to_bytes(self):
        return self.get_data()

# ISOM Defined Boxes

class FreeAtom(LazyLoadAtom):
    pass

class SkipAtom(LazyLoadAtom):
    pass

class MdatAtom(LazyLoadAtom):
    pass

class UserExtendedAtom(Atom):
    # TODO: How should I surface both uuid and the extended types
    def __init__(self, data, document, parent_atom, file_offset):
        Atom.__init__(self, data, document, parent_atom, file_offset)

        self._user_type = data[self._body_offset:self._body_offset+16]
        self._atom_body = data[self._body_offset+16:]

    def to_bytes(self):
        header_bytes = write_atom_header(self)
        return ''.join(header_bytes, self._user_type, self._atom_body)

class FtypAtom(Atom):
    def __init__(self, data, document, parent_atom, file_offset):
        Atom.__init__(self, data, document, parent_atom, file_offset)

        self.major_brand = data[self._body_offset:self._body_offset+4]
        self.minor_version = interpret_int32(data[self._body_offset+4:self._body_offset+8])

        self.compatible_brands = []
        pos = self._body_offset + 8
        while pos < self.size:
            self.compatible_brands.append(data[pos:pos+4])
            pos += 4

    def to_bytes(self):
        header_bytes = write_atom_header(self)
        minor_version_bytes = struct.pack(UINT_BYTES_TO_FORMAT[32], self.minor_version)
        box_sequence = chain([header_bytes, self.major_brand, minor_version_bytes], self.compatible_brands)
        return ''.join(box_sequence)


ATOM_TYPE_TO_CLASS = {
    'free': FreeAtom,
    'ftyp': FtypAtom,
    'mdat': MdatAtom,
    'skip': SkipAtom,
    'uuid': UserExtendedAtom,
}
