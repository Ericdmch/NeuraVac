"""Select locally reachable frontier and return goals from a full SLAM grid."""
import math
from .frontier_planner import plan_frontier
from .grid_geometry import route_to


class ExplorationPlanner:
    def __init__(self, geometry, rows, clearance_cells, rejected=None):
        if len(rows) != geometry.height or any(len(row) != geometry.width for row in rows):
            raise ValueError('Grid dimensions do not match geometry')
        self.geometry, self.rows, self.clearance = geometry, rows, clearance_cells
        # Store rejections in map coordinates so map origin changes don't shift them.
        self.rejected = set(rejected or ())

    def reject(self, point):
        self.rejected.add(tuple(point))

    def next_goal(self, position, min_distance_m=.2):
        if not math.isfinite(min_distance_m) or min_distance_m < 0:
            raise ValueError('Invalid minimum goal distance')
        start = self.geometry.world_cell(*position)
        if start is None or route_to(self.rows, start, start, self.clearance) is None:
            raise ValueError('Robot position is not in safely traversable known space')
        excluded = {cell for point in self.rejected
                    if (cell := self.geometry.world_cell(*point)) is not None}
        minimum = max(2, math.ceil(min_distance_m / self.geometry.resolution) + 1)
        path = plan_frontier(self.rows, start, self.clearance,
                             min_path_cells=minimum, excluded=excluded)
        return None if path is None else self.geometry.cell_center(path[-1])

    def return_reachable(self, position, return_goal):
        start = self.geometry.world_cell(*position)
        goal = self.geometry.world_cell(*return_goal)
        return route_to(self.rows, start, goal, self.clearance) is not None
