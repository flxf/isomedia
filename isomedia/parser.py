import os

from isomedia import atom
from isomedia.atom import GenericAtom, ContainerAtom
from isomedia.atom import interpret_atom_header, interpret_int32

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

def parse_file(ptr, document):
    atoms = []

    current_offset = 0
    filesize = get_ptr_size(ptr)

    while current_offset < filesize:
        new_atom, atom_size = parse_atom(ptr, document=document, parent=None, offset=current_offset)
        atoms.append(new_atom)
        current_offset += atom_size

    return atoms

def parse_atom(ptr, document=None, parent=None, offset=None):
    def parse_atom_header(ptr):
        data = need_read(ptr, 8)
        atom_size = interpret_int32(data, 0)
        if atom_size == 1:
            data += need_read(ptr, 8)

        return data

    atom_header = parse_atom_header(ptr)
    atom_type, atom_size, header_length = interpret_atom_header(atom_header)
    atom_body_length = atom_size - header_length

    if atom_type in atom.CONTAINER_ATOMS:
        new_atom = ContainerAtom(atom_header, document, parent, offset)
        new_atom.children = parse_children(ptr, atom_size - header_length, parent=new_atom, offset=offset + header_length)
    elif atom_type in atom.ATOM_TYPE_TO_CLASS:
        new_atom_class = atom.ATOM_TYPE_TO_CLASS[atom_type]
        if new_atom_class.LOAD_DATA:
            atom_body = need_read(ptr, atom_body_length)
        else:
            atom_body = ''
            ptr.seek(atom_body_length, os.SEEK_CUR)

        atom_data = atom_header + atom_body
        new_atom = new_atom_class(atom_data, document, parent, offset)
    else:
        atom_body = need_read(ptr, atom_size - header_length)
        atom_data = atom_header + atom_body
        new_atom = GenericAtom(atom_data, document, parent, offset)

    return (new_atom, atom_size)

def parse_children(ptr, total_bytes, parent=None, offset=None):
    children = []
    bytes_read = 0

    while bytes_read < total_bytes:
        new_atom, atom_size = parse_atom(ptr, parent=parent, offset=offset + bytes_read)
        children.append(new_atom)
        bytes_read += atom_size

    if bytes_read != total_bytes:
        raise Exception

    return children
