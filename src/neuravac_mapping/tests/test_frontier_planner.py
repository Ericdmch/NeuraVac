"""Frontier routes must stay in reachable, sufficiently clear known space."""
import unittest
from neuravac_mapping.frontier_planner import plan_frontier


class FrontierPlannerTests(unittest.TestCase):
    def test_routes_to_reachable_free_frontier(self):
        rows = [[100, 100, 100, 100, 100, 100],
                [100, 0, 0, 0, -1, 100],
                [100, 0, 0, 0, -1, 100],
                [100, 100, 100, 100, 100, 100]]
        path = plan_frontier(rows, (1, 1), clearance_cells=0)
        self.assertEqual(path[0], (1, 1))
        self.assertEqual(path[-1][0], 3)
        self.assertTrue(all(rows[y][x] == 0 for x, y in path))

    def test_refuses_unknown_or_occupied_start_and_no_frontier(self):
        rows = [[100, 100, 100], [100, 0, 100], [100, 100, 100]]
        self.assertIsNone(plan_frontier(rows, (1, 1), 0))
        self.assertIsNone(plan_frontier(rows, (0, 0), 0))
        self.assertIsNone(plan_frontier([[0, -1]], (1, 0), 0))

    def test_clearance_blocks_narrow_passage_and_unknown_is_not_traversed(self):
        rows = [[100, 100, 100, 100, 100], [100, 0, 0, -1, 100],
                [100, 100, 100, 100, 100]]
        self.assertIsNone(plan_frontier(rows, (1, 1), 1))
        self.assertIsNone(plan_frontier([[0, -1, 0, -1]], (0, 0), 1))

    def test_footprint_remains_in_known_free_space_near_frontier(self):
        rows = [[100] * 8, [100, 0, 0, 0, 0, -1, -1, 100],
                [100, 0, 0, 0, 0, -1, -1, 100],
                [100, 0, 0, 0, 0, -1, -1, 100], [100] * 8]
        path = plan_frontier(rows, (2, 2), 1)
        self.assertEqual(path[-1], (3, 2))
        for x, y in path:
            for dx, dy in ((0, 0), (0, 1), (0, -1), (1, 0), (-1, 0)):
                self.assertEqual(rows[y + dy][x + dx], 0)

    def test_rejects_malformed_grids(self):
        with self.assertRaises(ValueError):
            plan_frontier([[0], [0, 0]], (0, 0), 0)
        with self.assertRaises(ValueError):
            plan_frontier([[0]], (0, 0), -1)

class FrontierSelectionTests(unittest.TestCase):
    def test_can_exclude_failed_goal_and_avoid_selecting_current_cell(self):
        rows = [[100, 100, 100, 100, 100, 100],
                [100, -1, 0, 0, -1, 100],
                [100, 100, 100, 100, 100, 100]]
        path = plan_frontier(rows, (2, 1), 0, min_path_cells=2)
        self.assertEqual(path[-1], (3, 1))
        self.assertIsNone(plan_frontier(rows, (2, 1), 0, min_path_cells=2,
                                       excluded={(3, 1)}))
