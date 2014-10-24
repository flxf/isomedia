import filecmp
import os
import tempfile
import unittest

import isomedia
from isomedia.atom import GenericAtom

TESTDATA = os.path.join(os.path.dirname(__file__), 'testdata')

class TestSanity(unittest.TestCase):
    def test_sanity(self):
        mp4filename = os.path.join(TESTDATA, 'loop_circle.mp4')

        with open(mp4filename, 'rb') as mp4file:
            isofile = isomedia.load(mp4file)

            moov_atom = [atom for atom in isofile.atoms if atom.type == 'moov']
            self.assertEqual(len(moov_atom), 1, 'there should be 1 moov atom.')

    def test_lossless_write(self):
        mp4filename = os.path.join(TESTDATA, 'loop_circle.mp4')

        with open(mp4filename, 'rb') as infile, tempfile.NamedTemporaryFile(delete=False) as outfile:
            isofile = isomedia.load(infile)
            isofile.write(outfile)

        self.assertTrue(filecmp.cmp(infile.name, outfile.name))

        os.remove(outfile.name)

    def test_fail_to_generic_atom(self):
        mp4filename = os.path.join(TESTDATA, 'broken_mvhd.mp4')

        with open(mp4filename, 'rb') as infile:
            isofile = isomedia.load(infile)

            self.assertTrue(isofile.atoms)
            self.assertEqual(len(isofile.atoms), 1)
            self.assertTrue(isinstance(isofile.atoms[0], GenericAtom))

if __name__ == '__main__':
    unittest.main()
