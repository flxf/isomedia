from isomedia.atom import ContainerAtom
from isomedia.parser import parse_file

class ISOBaseMediaFile(object):
    def __init__(self, fp):
        self.fp = fp
        self.root = parse_file(fp)

    def __write_atom(self, atom, fp):
        if atom.type() != 'root-fakeatom':
            fp.write(atom.data)

        if isinstance(atom, ContainerAtom):
            for child in atom.children:
                self.__write_atom(child, fp)

    def write(self, fp=None):
        fp = fp or self.fp
        self.__write_atom(self.root, fp)

    def __repr__(self):
        return str(self.root)

def load(fp):
    return ISOBaseMediaFile(fp)
