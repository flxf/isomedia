from isomedia.atom import ContainerAtom, write_atom_header
from isomedia.exceptions import MalformedIsomFile
from isomedia.parser import parse_file

CHUNK_SIZE = 1024

class ISOBaseMediaFile(object):
    def __init__(self, fp):
        self.fp = fp
        self.atoms = parse_file(fp, self)

    def __write_atom(self, atom, fp):
        if isinstance(atom, ContainerAtom):
            fp.write(write_atom_header(atom))

            for child in atom.children:
                self.__write_atom(child, fp)
        else:
            if atom.LOAD_DATA:
                fp.write(atom.to_bytes())
            else:
                # Lazy-loaded Atoms are read-and-copy only.
                self.fp.seek(atom._input_file_offset)
                remaining_to_read = atom.size

                while remaining_to_read > 0:
                    next_chunk_length = min(CHUNK_SIZE, remaining_to_read)
                    fp.write(self.fp.read(next_chunk_length))
                    remaining_to_read -= next_chunk_length

    def write(self, fp):
        for atom in self.atoms:
            self.__write_atom(atom, fp)

    def __repr__(self):
        return str(self.atoms)

def load(fp):
    return ISOBaseMediaFile(fp)
