import unittest
from neuravac_mapping.exploration import ExplorationPlanner
from neuravac_mapping.grid_geometry import GridGeometry


class ExplorationTests(unittest.TestCase):
    def test_goal_in_map_frame_and_failed_goal_is_not_retried(self):
        rows = [[100, 100, 100, 100, 100, 100],
                [100, -1, 0, 0, -1, 100],
                [100, 100, 100, 100, 100, 100]]
        planner = ExplorationPlanner(GridGeometry(6, 3, 1., 3., 4., 0.), rows, 0)
        goal = planner.next_goal((5.5, 5.5), min_distance_m=.1)
        self.assertEqual(goal, (6.5, 5.5))
        planner.reject(goal)
        self.assertIsNone(planner.next_goal((5.5, 5.5), min_distance_m=.1))

    def test_blocked_start_is_not_successful_completion(self):
        geometry = GridGeometry(3, 3, 1., 0., 0., 0.)
        planner = ExplorationPlanner(geometry, [[100]*3, [100, 0, 100], [100]*3], 0)
        with self.assertRaises(ValueError):
            planner.next_goal((.5, .5))
        self.assertIsNone(planner.next_goal((1.5, 1.5)))

    def test_return_goal_must_be_reachable_known_free_space(self):
        geometry = GridGeometry(4, 1, 1., 0., 0., 0.)
        planner = ExplorationPlanner(geometry, [[0, 0, -1, 0]], 0)
        self.assertTrue(planner.return_reachable((.5, .5), (1.5, .5)))
        self.assertFalse(planner.return_reachable((.5, .5), (3.5, .5)))
