"""Checks independent of Houdini: exact areas, exposed edges and door access."""
import unittest
from terrace_layout import modules, terrace_regions, area, frontage_access, support_segments


class LayoutChecks(unittest.TestCase):
    def test_equal_floors_have_no_terraces(self):
        r=[(-5,5,-4,4)]
        self.assertEqual(terrace_regions(r,r),([],[]))

    def test_setback_leaves_deck_and_three_open_edges(self):
        deck,rails=terrace_regions([(0,10,0,10)],[(0,10,0,8)])
        self.assertAlmostEqual(area(deck),20.)
        self.assertEqual(len(rails),3)
        # The fourth boundary contacts a wall and must stay open to its door.
        self.assertFalse(any(z0==8 and z1==8 for x0,z0,x1,z1 in rails))

    def test_larger_upper_floor_cannot_create_lower_terraces(self):
        self.assertEqual(terrace_regions([(-4,4,-4,4)],[(-5,5,-5,5)]),([],[]))

    def test_adjacent_lower_modules_have_no_internal_rail(self):
        deck,rails=terrace_regions([(0,5,0,10),(5,10,0,10)],[(0,10,0,8)])
        self.assertAlmostEqual(area(deck),20.)
        self.assertEqual(len(rails),3)
        self.assertFalse(any(x0==5 and x1==5 for x0,z0,x1,z1 in rails))

    def test_checkerboard_has_known_exposed_area(self):
        lower=[m['rect'] for m in modules(24,10,6,parity=0)]
        upper=[m['rect'] for m in modules(24,10,6,parity=1)]
        self.assertAlmostEqual(area(terrace_regions(lower,upper)[0]),28.8)

    def test_access_requires_usable_deck_outside_door(self):
        module={'rect':(0,4,0,8)}
        self.assertTrue(frontage_access(module,[(0,4,0,10)]))
        self.assertFalse(frontage_access(module,[(0,4,0,8)]))
        self.assertFalse(frontage_access(module,[(0,4,0,8.2)]))

    def test_supports_exist_for_overhang_but_not_contained_floor(self):
        self.assertTrue(support_segments([(-5,5,-5,5)],[(-4,4,-4,4)]))
        self.assertEqual(support_segments([(-4,4,-4,4)],[(-5,5,-5,5)]),[])


if __name__=='__main__':
    unittest.main()
