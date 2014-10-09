import unittest

from isomedia import isomedia
import os

TESTDATA = os.path.join(os.path.dirname(__file__), 'testdata')

class TestSanity(unittest.TestCase):
    def test_sanity(self):
        mp4filename = os.path.join(TESTDATA, 'loop_circle.mp4')
        mp4file = open(mp4filename, 'rb')
        isofile = isomedia.load(mp4file)

        moov_atom = [atom for atom in isofile.atoms if atom.type() == 'moov']
        self.assertEqual(len(moov_atom), 1, 'There should be 1 moov atom.')

if __name__ == '__main__':
    unittest.main()
