from itertools import chain
import StringIO
import struct

from isomedia.exceptions import AtomSpecificationError

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
    'edts',
    'egid',
    'extr',
    'fiin',
    'gnre',
    'ilst',
    'ipro',
    'keyw',
    'mdia',
    'meta',
    'meco',
    'mfra',
    'minf',
    'moof',
    'moov',
    'mvex',
    'paen',
    'pcst',
    'pgap',
    'purd',
    'purl',
    'rinf',
    'rtng',
    'schi',
    'sinf',
    'srpp',
    'stik',
    'strd',
    'strk',
    'stbl',
    'tmpo',
    'traf',
    'trak',
    'tref',
    'trkn',
    'tven',
    'tves',
    'tvnn',
    'tvsh',
    'tvsn',
    'udta',
]

UINT_BYTES_TO_FORMAT = {
    1: '>B',
    2: '>H',
    4: '>I',
    8: '>Q'
}

MAX_UINT32 = (2 ** 32) - 1
STANDARD_HEADER_LENGTH = 8
EXTENDED_HEADER_LENGTH = 16

def interpret_int(data, offset, size):
    assert size in UINT_BYTES_TO_FORMAT
    field = data[offset:offset + size]
    return struct.unpack(UINT_BYTES_TO_FORMAT[size], field)[0]

def interpret_int64(data, offset=0):
    return interpret_int(data, offset, 8)

def interpret_int32(data, offset=0):
    return interpret_int(data, offset, 4)

def interpret_int16(data, offset=0):
    return interpret_int(data, offset, 2)

def interpret_int8(data, offset=0):
    return interpret_int(data, offset, 1)

def write_atom_header(atom):
    header_bytes = ''

    if atom.size > MAX_UINT32:
        header_bytes += struct.pack(UINT_BYTES_TO_FORMAT[4], 1)
    else:
        header_bytes += struct.pack(UINT_BYTES_TO_FORMAT[4], atom.size)
    header_bytes += atom.type
    if atom.size > MAX_UINT32:
        header_bytes += struct.pack(UINT_BYTES_TO_FORMAT[8], atom.size)

    return header_bytes

def interpret_atom(atom_body, definition):
    def cast_field(data, size, cast):
        if cast == int:
            data = interpret_int(data, 0, size)
        return data

    result = {}

    for field in definition:
        field_name, field_type = field
        length = field_type[0]

        if length == list:
            item_length, item_cast = field_type[1]
            item_count = field_type[2]

            data = []
            while item_count is None or len(data) < item_count:
                item_data = atom_body.read(item_length)
                if not item_data:
                    break
                elif len(item_data) != item_length:
                    raise AtomSpecificationError

                item_data = cast_field(item_data, item_length, item_cast)
                data.append(item_data)

        else:
            data = atom_body.read(length)
            if len(data) != length:
                raise AtomSpecificationError

            cast = field_type[1]
            data = cast_field(data, length, cast)

        result[field_name] = data

    return result

def write_atom(properties, definition):
    result = ''

    for field in definition:
        field_name, field_type = field
        field_value = properties[field_name]

        length = field_type[0]

        if length == list:
            item_length, item_cast = field_type[1]

            for item_value in field_value:
                if item_cast == int:
                    result += struct.pack(UINT_BYTES_TO_FORMAT[item_length], item_value)
                else:
                    result += item_value
        else:
            cast = field_type[1]
            if cast == int:
                result += struct.pack(UINT_BYTES_TO_FORMAT[length], field_value)
            else:
                result += field_value

    return result

class AtomHeader(object):
    def __init__(self, atom_type, atom_size, header_length):
        self.type = atom_type
        self.size = atom_size
        self.header_length = header_length

class Atom(object):
    # Allow lazy-loading (enabled when False)
    LOAD_DATA = True

    def __init__(self, atom_header, atom_body, document, parent_atom, file_offset):
        self.header = atom_header

        self.document = document
        self.parent_atom = parent_atom

        self._input_file_offset = file_offset
        self._input_size = atom_header.size
        self._body_offset = atom_header.header_length

        self._definition = {}
        self.properties = {}

    def to_bytes(self):
        return write_atom_header(self)

    def __repr__(self):
        return str({
            'type': self.type
        })

    @property
    def type(self):
        return self.header.type

    @type.setter
    def type(self, value):
        assert isinstance(value, str), 'A box\'s type field should be a string.'
        assert len(value) == 4, 'A box\'s type should be 4 bytes exactly.'
        self.header.type = value

    @property
    def size(self):
        return self.header.size

    @size.setter
    def size(self, value):
        self.header.size = value

class FullAtom(Atom):
    def __init__(self, atom_header, atom_body, document, parent_atom, file_offset):
        Atom.__init__(self, atom_header, atom_body, document, parent_atom, file_offset)

        definition = [
            ('version', (1, int)),
            ('flags', (3, None))
        ]

        self.properties.update(interpret_atom(atom_body, definition))
        self._definition['FullAtom'] = definition

    def to_bytes(self):
        written = Atom.to_bytes(self)
        return ''.join([written, write_atom(self.properties, self._definition['FullAtom'])])

class ContainerAtom(Atom):
    def __init__(self, atom_header, atom_body, document, parent_atom, file_offset):
        Atom.__init__(self, atom_header, atom_body, document, parent_atom, file_offset)
        self.children = []

    def __repr__(self):
        return str({
            'type': self.type,
            'children': self.children
        })

    def to_bytes(self):
        written = Atom.to_bytes(self)
        return ''.join(chain([written], (child.to_bytes() for child in self.children)))

    def append_child(self, child):
        self.size += child.size
        self.children.append(child)

class GenericAtom(Atom):
    def __init__(self, atom_header, atom_body, document, parent_atom, file_offset):
        Atom.__init__(self, atom_header, atom_body, document, parent_atom, file_offset)
        self._data = atom_body.read()

    def get_data(self):
        return self._data

    def to_bytes(self):
        written = Atom.to_bytes(self)
        return ''.join([written, self.get_data()])

class LazyLoadAtom(Atom):
    LOAD_DATA = False

    def __init__(self, atom_header, atom_body, document, parent_atom, file_offset):
        Atom.__init__(self, atom_header, atom_body, document, parent_atom, file_offset)
        self._data = None

    def get_data(self):
        if self._data is None:
            fp = self.document.fp
            fp.seek(self._input_file_offset + self._body_offset)
            self._data = fp.read(self._input_size - self._body_offset)

        return self._data

    def to_bytes(self):
        written = Atom.to_bytes(self)
        return ''.join([written, self.get_data()])

def create_atom(atom_type, atom_body):
    body_length = len(atom_body)
    if body_length + STANDARD_HEADER_LENGTH <= MAX_UINT32:
        header_length = STANDARD_HEADER_LENGTH
    else:
        header_length = EXTENDED_HEADER_LENGTH

    atom_size = header_length + body_length
    atom_header = AtomHeader(None, atom_size, header_length)
    atom = GenericAtom(atom_header, StringIO.StringIO(atom_body), None, None, None)
    atom.type = atom_type

    return atom
