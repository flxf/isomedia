from itertools import chain
import struct

ISOM_BOXES = [
    'bxml',
    'co64',
    'cprt',
    'cslg',
    'ctts',
    'dinf',
    'dref',
    'edts',
    'elst',
    'fecr',
    'fiin',
    'fire',
    'fpar',
    'free',
    'frma',
    'ftyp',
    'gitn',
    'hdlr',
    'hmhd',
    'idat',
    'iinf',
    'iloc',
    'ipro',
    'iref',
    'leva',
    'mdat',
    'mdhd',
    'mdia',
    'meco',
    'mehd',
    'mere',
    'meta',
    'mfhd',
    'mfra',
    'mfro',
    'minf',
    'moof',
    'moov',
    'mvex',
    'mvhd',
    'nmhd',
    'padb',
    'paen',
    'pdin',
    'pitm',
    'prft',
    'saio',
    'saiz',
    'sbgp',
    'schi',
    'schm',
    'sdtp',
    'segr',
    'sgpd',
    'sidx',
    'sinf',
    'skip',
    'smhd',
    'ssix',
    'stbl',
    'stco',
    'stdp',
    'strd',
    'stri',
    'strk',
    'stsc',
    'stsd',
    'stsh',
    'stss',
    'stsz',
    'stts',
    'styp',
    'stz2',
    'subs',
    'tfdt',
    'tfhd',
    'tfra',
    'tkhd',
    'traf',
    'trak',
    'tref',
    'trex',
    'trgr',
    'trun',
    'tsel',
    'udta',
    'vmhd',
    'xml ',
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

def write_atom_header(atom):
    header = atom.header
    header_bytes = ''

    if header.size >= MAX_UINT32:
        header_bytes += struct.pack(UINT_BYTES_TO_FORMAT[32], 1)
    else:
        header_bytes += struct.pack(UINT_BYTES_TO_FORMAT[32], atom.size)
    header_bytes += header.type
    if header.size >= MAX_UINT32:
        header_bytes += struct.pack(UINT_BYTES_TO_FORMAT[64], atom.size)

    return header_bytes

class AtomHeader(object):
    def __init__(self, atom_type, atom_size, header_length):
        self.type = atom_type
        self.size = atom_size
        self.header_length = header_length

class Atom(object):
    # Enable lazy-loading
    LOAD_DATA = True

    def __init__(self, atom_header, atom_body, document, parent_atom, file_offset):
        self.header = atom_header

        self.document = document
        self.parent_atom = parent_atom

        self._input_file_offset = file_offset
        self._input_size = atom_header.size
        self._body_offset = atom_header.header_length

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

    def to_bytes(self):
        raise NotImplementedError

class FullAtom(Atom):
    def __init__(self, atom_header, atom_body, document, parent_atom, file_offset):
        Atom.__init__(self, atom_header, atom_body, document, parent_atom, file_offset)

        # Can a full-box have an extended header?
        self.version = interpret_int8(atom_body)
        self.flags = atom_body[1:4]

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
        header_bytes = write_atom_header(self)
        return ''.join(chain(header_bytes, (child.to_bytes() for child in self.children)))

    def append_child(self, child):
        self.size += child.size
        self.children.append(child)

class GenericAtom(Atom):
    def __init__(self, atom_header, atom_body, document, parent_atom, file_offset):
        Atom.__init__(self, atom_header, atom_body, document, parent_atom, file_offset)
        self._data = atom_body

    def get_data(self):
        return self._data

    def to_bytes(self):
        header_bytes = write_atom_header(self)
        return header_bytes + self.get_data()

class LazyLoadAtom(Atom):
    LOAD_DATA = False

    def __init__(self, atom_header, atom_body, document, parent_atom, file_offset):
        Atom.__init__(self, atom_header, atom_body, document, parent_atom, file_offset)
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
    def __init__(self, atom_header, atom_body, document, parent_atom, file_offset):
        Atom.__init__(self, atom_header, atom_body, document, parent_atom, file_offset)

        self._user_type = atom_body[0:16]
        self._data = atom_body

    def to_bytes(self):
        header_bytes = write_atom_header(self)
        return ''.join(header_bytes, self._data)

class FtypAtom(Atom):
    DEFINITION = {
        'major_brand': (4, None),
        'minor_version': (4, int),
        'compatible_brands': (list, (4, None))
    }

    def __init__(self, atom_header, atom_body, document, parent_atom, file_offset):
        Atom.__init__(self, atom_header, atom_body, document, parent_atom, file_offset)

        self.major_brand = atom_body[0:4]
        self.minor_version = interpret_int32(atom_body[4:8])

        self.compatible_brands = []
        pos = 8

        while pos < self.size:
            self.compatible_brands.append(atom_body[pos:pos+4])
            pos += 4

    def to_bytes(self):
        header_bytes = write_atom_header(self)
        minor_version_bytes = struct.pack(UINT_BYTES_TO_FORMAT[32], self.minor_version)
        box_sequence = chain([header_bytes, self.major_brand, minor_version_bytes], self.compatible_brands)
        return ''.join(box_sequence)

class MvhdAtom(FullAtom):
    def __init__(self, atom_header, atom_body, document, parent_atom, file_offset):
        FullAtom.__init__(self, atom_header, atom_body, document, parent_atom, file_offset)

        if self.version == 1:
            self.creation_time = interpret_int64(atom_body, offset=4)
            self.modification_time = interpret_int64(atom_body, offset=12)
            self.timescale = interpret_int32(atom_body, offset=20)
            self.duration = interpret_int64(atom_body, offset=24)
        else:
            self.creation_time = interpret_int32(atom_body, offset=4)
            self.modification_time = interpret_int32(atom_body, offset=8)
            self.timescale = interpret_int32(atom_body, offset=12)
            self.duration = interpret_int32(atom_body, offset=16)

    def to_bytes(self):
        header_bytes = write_atom_header(self)
        full_atom_bytes = struct.pack(UINT_BYTES_TO_FORMAT[8], self.version) + self.flags

        contents_format = '>Q>Q>I>Q' if self.version == 1 else '>I>I>I>I'
        contents_bytes = struct.pack(
            contents_format, self.creation_time, self.modification_time, self.timescale, self.duration)

        return ''.join(chain(header_bytes, full_atom_bytes, contents_bytes))

ATOM_TYPE_TO_CLASS = {
    'free': FreeAtom,
    'ftyp': FtypAtom,
    'mdat': MdatAtom,
    'mvhd': MvhdAtom,
    'skip': SkipAtom,
    'uuid': UserExtendedAtom,
}
