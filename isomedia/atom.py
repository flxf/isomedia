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

class Atom(object):
    def __init__(self, data, parent_atom, offset, size):
        self.data = data
        self.type = data[4:8]
        self.offset = offset
        self.size = size
        self.parent_atom = parent_atom

    def __repr__(self):
        return str({
            'type': self.type
        })

class ContainerAtom(Atom):
    def __init__(self, data, parent_atom, offset, size):
        Atom.__init__(self, data, parent_atom, offset, size)
        self.children = []

    def __repr__(self):
        return str({
            'type': self.data[4:8],
            'children': self.children
        })
