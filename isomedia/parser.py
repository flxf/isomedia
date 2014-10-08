import struct
import os

import atom
from atom import Atom, ContainerAtom

def read64(ptr):
    data = ptr.read(8)
    if data is None or len(data) != 8:
        raise Exception
    return struct.unpack('>Q', data)[0]

def read32(ptr):
    data = ptr.read(4)
    if data is None or len(data) != 4:
        raise Exception
    return struct.unpack('>I', data)[0]

def read16(ptr):
    data = ptr.read(2)
    if data is None or len(data) != 2:
        raise Exception
    return struct.unpack('>H', data)[0]

def read8(ptr):
    data = ptr.read(1)
    if data is None or len(data) != 1:
        raise Exception
    return struct.unpack('>B', data)[0]

def parse_file(ptr, filesize):
    return parse_children(ptr, filesize)

def parse_atom_header(ptr):
    header_size = 8 # bytes
    atom_size = read32(ptr)
    atom_type = ptr.read(4)
    if atom_size == 1:
        atom_size = read64(ptr)
        header_size = 16 # bytes
    return (atom_type, atom_size, header_size)

def parse_atom(ptr):
    atom_type, atom_size, header_size = parse_atom_header(ptr)
    ptr.seek(-header_size, os.SEEK_CUR)

    if atom_type in atom.CONTAINER_ATOMS:
        atom_data = ptr.read(header_size)
        new_atom = ContainerAtom(atom_data, None, 0, atom_size)
        new_atom.children = parse_children(ptr, atom_size - header_size)
    else:
        new_atom = Atom(ptr.read(atom_size), None, 0, atom_size)

    return (new_atom, atom_size)

def parse_children(ptr, total_bytes):
    children = []
    bytes_read = 0

    while bytes_read < total_bytes:
        new_atom, atom_size = parse_atom(ptr)
        children.append(new_atom)
        bytes_read += atom_size

    return children
