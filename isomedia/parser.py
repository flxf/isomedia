import os
import StringIO

from isomedia import atom, isom_atoms
from isomedia.atom import AtomHeader, ContainerAtom, ContainerMixin, GenericAtom, interpret_int32, interpret_int64
from isomedia.exceptions import MalformedIsomFile, AtomSpecificationError

def get_ptr_size(ptr):
    ptr.seek(0, os.SEEK_END)
    size = ptr.tell()
    ptr.seek(0, os.SEEK_SET)
    return size

def need_read(ptr, n):
    data = ptr.read(n)
    if data is None or len(data) != n:
        raise EOFError
    return data

def interpret_atom_header(data):
    atom_size = interpret_int32(data, 0)
    atom_type = data[4:8]

    if atom_size == 1:
        atom_size = interpret_int64(data, 8)
        header_length = 16
    else:
        header_length = 8

    return (atom_type, atom_size, header_length)

def parse_file(ptr, document):
    atoms = []

    current_offset = 0
    filesize = get_ptr_size(ptr)

    while current_offset < filesize:
        new_atom, atom_size = parse_atom(ptr, current_offset, document=document, parent=None)
        atoms.append(new_atom)
        current_offset += atom_size

    return atoms

def parse_atom(ptr, offset, document=None, parent=None):
    def parse_atom_header(ptr):
        data = need_read(ptr, 8)
        atom_size = interpret_int32(data, 0)
        if atom_size == 1:
            data += need_read(ptr, 8)

        return data

    try:
        atom_header = parse_atom_header(ptr)
    except EOFError:
        raise MalformedIsomFile

    atom_type, atom_size, header_length = interpret_atom_header(atom_header)

    atom_header = AtomHeader(atom_type, atom_size, header_length)
    atom_body_length = atom_size - header_length
    atom_body_start = ptr.tell()

    # TODO: Clearly distinguish different atom specifications
    new_atom = None

    if atom_type in atom.CONTAINER_ATOMS:
        new_atom = ContainerAtom(atom_header, ptr, document, parent, offset)
        new_atom.children = parse_children(ptr, offset + header_length, atom_body_length, parent=new_atom)
    elif atom_type in isom_atoms.ATOM_TYPE_TO_CLASS:
        new_atom_class = isom_atoms.ATOM_TYPE_TO_CLASS[atom_type]

        if new_atom_class.LOAD_DATA:
            # If the atom is the right size but doesn't match the definition, we can still parse the rest of the file and
            # just default this atom to a GenericAtom and let the caller munge the bits.
            try:
                new_atom = new_atom_class(atom_header, ptr, document, parent, offset)
                parent_fragment_bytes = ptr.tell() - atom_body_start
                children_bytes = atom_size - header_length - parent_fragment_bytes

                if isinstance(new_atom, ContainerMixin):
                    new_atom.children = parse_children(ptr, offset + header_length, children_bytes, parent=new_atom)
            except AtomSpecificationError:
                new_atom = None
                ptr.seek(atom_body_start, os.SEEK_SET)
        else:
            new_atom = new_atom_class(atom_header, ptr, document, parent, offset)
            ptr.seek(atom_body_length, os.SEEK_CUR)

    if new_atom is None:
        generic_data = ptr.read(atom_body_length)
        new_atom = GenericAtom(atom_header, StringIO.StringIO(generic_data), document, parent, offset)

    atom_body_end = ptr.tell()
    atom_bytes_read = header_length + (atom_body_end - atom_body_start)

    if atom_bytes_read != atom_size:
        raise MalformedIsomFile

    return (new_atom, atom_size)

def parse_children(ptr, offset, total_bytes, parent=None):
    children = []
    bytes_read = 0

    while bytes_read < total_bytes:
        new_atom, atom_size = parse_atom(ptr, offset + bytes_read, parent=parent)
        children.append(new_atom)
        bytes_read += atom_size

    if bytes_read != total_bytes:
        raise MalformedIsomFile

    return children
