from isomedia.atom import Atom, ContainerMixin, FullAtom, LazyLoadAtom, interpret_atom, write_atom

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
        super(UserExtendedAtom, self).__init__(atom_header, atom_body, document, parent_atom, file_offset)

        self._user_type = atom_body[0:16]
        self._data = atom_body

    def get_data(self):
        return self._data

    def to_bytes(self):
        written = super(UserExtendedAtom, self).to_bytes()
        return ''.join([written, self.get_data()])

class FtypAtom(Atom):
    def __init__(self, atom_header, atom_body, document, parent_atom, file_offset):
        super(FtypAtom, self).__init__(atom_header, atom_body, document, parent_atom, file_offset)

        definition = [
            ('major_brand', (4, None)),
            ('minor_version', (4, int)),
            ('compatible_brands', (list, (4, None), None))
        ]

        self.properties.update(interpret_atom(atom_header, atom_body, definition))
        self._definition['FtypAtom'] = definition

    def to_bytes(self):
        written = super(FtypAtom, self).to_bytes()
        return ''.join([written, write_atom(self.properties, self._definition['FtypAtom'])])

class IlstAtom(ContainerMixin, Atom):
    def __init__(self, atom_header, atom_body, document, parent_atom, file_offset):
        super(IlstAtom, self).__init__(atom_header, atom_body, document, parent_atom, file_offset)

        definition = [
            ('tag_name', (4, None)),
        ]

        self.properties.update(interpret_atom(atom_header, atom_body, definition))
        self._definition['IlstAtom'] = definition

    def to_bytes(self):
        written = super(IlstAtom, self).to_bytes()
        return ''.join([written, write_atom(self.properties, self._definition['IlstAtom'])])


class MvhdAtom(FullAtom):
    def __init__(self, atom_header, atom_body, document, parent_atom, file_offset):
        super(MvhdAtom, self).__init__(atom_header, atom_body, document, parent_atom, file_offset)

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

        self.properties.update(interpret_atom(atom_header, atom_body, definition))
        self._definition['MvhdAtom'] = definition

    def to_bytes(self):
        written = super(MvhdAtom, self).to_bytes()
        return ''.join([written, write_atom(self.properties, self._definition['MvhdAtom'])])

class MetaAtom(ContainerMixin, FullAtom):
    pass

ATOM_TYPE_TO_CLASS = {
    'free': FreeAtom,
    'ftyp': FtypAtom,
    'ilst': IlstAtom,
    'mdat': MdatAtom,
    'meta': MetaAtom,
    'mvhd': MvhdAtom,
    'skip': SkipAtom,
    'uuid': UserExtendedAtom,
}
