from isomedia.atom import ContainerAtom
from isomedia.atom import interpret_atom_header
from isomedia.parser import parse_file

CHUNK_SIZE = 1024

class ISOBaseMediaFile(object):
    def __init__(self, fp):
        self.fp = fp
        self.atoms = parse_file(fp, self)

    def __write_atom(self, atom, fp):
        if atom.LOAD_DATA:
            fp.write(atom._data)
        else:
            # Lazy-loaded Atoms are read-and-copy only.
            self.fp.seek(atom._input_file_offset)
            remaining_to_read = atom.size()

            while remaining_to_read > 0:
                next_chunk_length = min(CHUNK_SIZE, remaining_to_read)
                fp.write(self.fp.read(next_chunk_length))
                remaining_to_read -= next_chunk_length

        if isinstance(atom, ContainerAtom):
            for child in atom.children:
                self.__write_atom(child, fp)

    def __save_atom(self, atom, fp):
        raise NotImplementedError

    # write dumps the entire contents of the tree to a file. save takes no arguments and is used to make in-place
    # modifications to a file.

    def write(self, fp):
        for atom in self.atoms:
            self.__write_atom(atom, fp)

    def save(self):
        for atom in self.atoms:
            self.__save_atom(atom, self.fp)

    def __repr__(self):
        return str(self.atoms)

def load(fp):
    return ISOBaseMediaFile(fp)
