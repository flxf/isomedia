import filecmp
import os
import tempfile
import unittest

import isomedia

TESTDATA = os.path.join(os.path.dirname(__file__), 'testdata')

class TestSanity(unittest.TestCase):
    def test_sanity(self):
        mp4filename = os.path.join(TESTDATA, 'loop_circle.mp4')
        mp4file = open(mp4filename, 'rb')
        isofile = isomedia.load(mp4file)

        root = isofile.root
        moov_atom = [atom for atom in root.children if atom.type() == 'moov']
        self.assertEqual(len(moov_atom), 1, 'There should be 1 moov atom.')

    def test_lossless_write(self):
        mp4filename = os.path.join(TESTDATA, 'loop_circle.mp4')
        infile = open(mp4filename, 'rb')
        isofile = isomedia.load(infile)

        outfile = tempfile.NamedTemporaryFile(delete=False)
        isofile.write(outfile)

        infile.close()
        outfile.close()

        self.assertTrue(filecmp.cmp(infile.name, outfile.name))

if __name__ == '__main__':
    unittest.main()
