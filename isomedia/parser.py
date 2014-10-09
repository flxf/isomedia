import atom
from atom import Atom, ContainerAtom
from atom import interpret_atom_header, interpret_int32

def need_read(ptr, n):
    data = ptr.read(n)
    if data is None or len(data) != n:
        raise EOFError
    return data

def parse_file(ptr):
    children = []
    current_offset = 0

    while True:
        try:
            new_atom, atom_size = parse_atom(ptr, parent=None, offset=current_offset)
            children.append(new_atom)
            current_offset += atom_size
        except EOFError:
            break

    return children


def parse_atom(ptr, parent=None, offset=None):
    def parse_atom_header(ptr):
        data = need_read(ptr, 8)
        atom_size = interpret_int32(data, 0)
        if atom_size == 1:
            data += need_read(ptr, 8)

        return data

    atom_header = parse_atom_header(ptr)
    header_size = len(atom_header)
    atom_type, atom_size = interpret_atom_header(atom_header)

    if atom_type in atom.CONTAINER_ATOMS:
        new_atom = ContainerAtom(atom_header, parent, offset)
        new_atom.children = parse_children(ptr, atom_size - header_size, parent=new_atom, offset=offset + header_size)
    else:
        atom_data = need_read(ptr, atom_size - header_size)
        atom_data = atom_header + atom_data
        new_atom = Atom(atom_data, parent, offset)

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
