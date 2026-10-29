import math
import unittest
from neuravac_mapping.grid_geometry import GridGeometry, route_to


class GridGeometryTests(unittest.TestCase):
    def test_round_trip_with_rotated_origin(self):
        grid = GridGeometry(10, 8, .1, 3., -2., math.pi / 2)
        world = grid.cell_center((2, 3))
        self.assertEqual(grid.world_cell(*world), (2, 3))
        self.assertIsNone(grid.world_cell(100, 100))

    def test_invalid_dimensions_and_nonfinite_points_rejected(self):
        with self.assertRaises(ValueError):
            GridGeometry(1, 1, 0, 0, 0, 0)
        grid = GridGeometry(2, 2, 1, 0, 0, 0)
        self.assertIsNone(grid.world_cell(float('nan'), 0))

    def test_route_avoids_unknown_and_respects_clearance(self):
        grid = [[100]*7, [100, 0, 0, 0, 0, -1, 100],
                [100, 0, 0, 0, 0, -1, 100], [100]*7]
        self.assertEqual(route_to(grid, (1, 1), (4, 1), 0)[-1], (4, 1))
        self.assertIsNone(route_to(grid, (1, 1), (5, 1), 0))
        self.assertIsNone(route_to(grid, (1, 1), (4, 1), 1))
