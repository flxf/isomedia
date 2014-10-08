from parser import parse_file
import os

from atom import ContainerAtom

class ISOBaseMediaFile(object):
    def __init__(self, fp):
        self.fp = fp

        fp.seek(0, os.SEEK_END)
        self.size = fp.tell()
        fp.seek(0)

        self.atoms = parse_file(fp, self.size)

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
