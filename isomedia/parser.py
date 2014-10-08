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

    while True:
        try:
            new_atom = parse_atom(ptr, parent=None)[0]
            children.append(new_atom)
        except EOFError:
            break

    return children

def parse_atom_header(ptr):
    data = need_read(ptr, 8)
    atom_size = interpret_int32(data, 0)
    if atom_size == 1:
        data += need_read(ptr, 8)

    return data

def parse_atom(ptr, parent=None):
    atom_header = parse_atom_header(ptr)
    atom_type, atom_size = interpret_atom_header(atom_header)

    if atom_type in atom.CONTAINER_ATOMS:
        new_atom = ContainerAtom(atom_header, parent)
        new_atom.children = parse_children(ptr, atom_size - len(atom_header), parent=new_atom)
    else:
        atom_data = need_read(ptr, atom_size - len(atom_header))
        atom_data = atom_header + atom_data
        new_atom = Atom(atom_data, parent)

    return (new_atom, atom_size)

def parse_children(ptr, total_bytes, parent=None):
    children = []
    bytes_read = 0

    while bytes_read < total_bytes:
        new_atom, atom_size = parse_atom(ptr, parent=parent)
        children.append(new_atom)
        bytes_read += atom_size

    return children
