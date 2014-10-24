from isomedia.atom import Atom, FullAtom, LazyLoadAtom, interpret_atom, write_atom

ISOM_ATOMS = [
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

    def get_data(self):
        return self._data

    def to_bytes(self):
        written = Atom.to_bytes(self)
        return ''.join([written, self.get_data()])

class FtypAtom(Atom):
    def __init__(self, atom_header, atom_body, document, parent_atom, file_offset):
        Atom.__init__(self, atom_header, atom_body, document, parent_atom, file_offset)

        definition = [
            ('major_brand', (4, None)),
            ('minor_version', (4, int)),
            ('compatible_brands', (list, (4, None), None))
        ]

        self.properties.update(interpret_atom(atom_body, definition))
        self._definition['FtypAtom'] = definition

    def to_bytes(self):
        written = Atom.to_bytes(self)
        return ''.join([written, write_atom(self.properties, self._definition['FtypAtom'])])

class MvhdAtom(FullAtom):
    def __init__(self, atom_header, atom_body, document, parent_atom, file_offset):
        FullAtom.__init__(self, atom_header, atom_body, document, parent_atom, file_offset)

        definition = []

        if self.properties['version'] == 1:
            definition.extend([
                ('creation_time', (8, int)),
                ('modification_time', (8, int)),
                ('timescale', (4, int)),
                ('duration', (8, int))
            ])
        else:
            definition.extend([
                ('creation_time', (4, int)),
                ('modification_time', (4, int)),
                ('timescale', (4, int)),
                ('duration', (4, int))
            ])

        definition.extend([
            ('rate', (4, int)),
            ('volume', (2, int)),
            ('reserved', (2, int)),
            ('preferred_long', (list, (4, int), 2)),
            ('matrix', (list, (4, int), 9)),
            ('preview_time', (4, int)),
            ('preview_duration', (4, int)),
            ('poster_time', (4, int)),
            ('selection_time', (4, int)),
            ('selection_duration', (4, int)),
            ('current_time', (4, int)),
            ('next_track_ID', (4, int))
        ])

        self.properties.update(interpret_atom(atom_body, definition))
        self._definition['MvhdAtom'] = definition

    def to_bytes(self):
        written = FullAtom.to_bytes(self)
        return ''.join([written, write_atom(self.properties, self._definition['MvhdAtom'])])

ATOM_TYPE_TO_CLASS = {
    'free': FreeAtom,
    'ftyp': FtypAtom,
    'mdat': MdatAtom,
    'mvhd': MvhdAtom,
    'skip': SkipAtom,
    'uuid': UserExtendedAtom,
}
