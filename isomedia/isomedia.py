from parser import parse_file

from atom import ContainerAtom

class ISOBaseMediaFile(object):
    def __init__(self, fp):
        self.fp = fp
        self.atoms = parse_file(fp)

    def __write_atom(self, atom, fp):
        fp.write(atom.data)
        if isinstance(atom, ContainerAtom):
            for child in atom.children:
                self.__write_atom(child, fp)

    def write(self, fp=None):
        fp = fp or self.fp

        for atom in self.atoms:
            self.__write_atom(atom, fp)

    def __repr__(self):
        return str({
            'atoms': self.atoms
        })

def load(fp):
    return ISOBaseMediaFile(fp)
