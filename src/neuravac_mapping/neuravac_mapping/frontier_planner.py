"""Select reachable frontiers in an occupancy grid, without commanding motion.

Coordinates are (column, row). Unknown and non-free cells are never entered.
Clearance is measured in grid cells; cells outside the map are obstacles.
"""
from collections import deque
from math import hypot


def plan_frontier(rows, start, clearance_cells, free_threshold=20, *,
                  min_path_cells=1, excluded=()):
    if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError('Grid must be rectangular and nonempty')
    if not isinstance(clearance_cells, int) or clearance_cells < 0:
        raise ValueError('Clearance must be a nonnegative integer')
    if not isinstance(min_path_cells, int) or min_path_cells < 1:
        raise ValueError('Minimum path length must be positive')
    excluded = set(excluded)
    height, width = len(rows), len(rows[0])
    if any(not isinstance(v, int) or v < -1 or v > 100 for row in rows for v in row):
        raise ValueError('Occupancy values must be integers from -1 to 100')

    def traversable(x, y):
        if not (0 <= x < width and 0 <= y < height) or not (0 <= rows[y][x] <= free_threshold):
            return False
        for dy in range(-clearance_cells, clearance_cells + 1):
            for dx in range(-clearance_cells, clearance_cells + 1):
                if hypot(dx, dy) > clearance_cells:
                    continue
                xx, yy = x + dx, y + dy
                if not (0 <= xx < width and 0 <= yy < height):
                    return False
                value = rows[yy][xx]
                if value < 0 or value > free_threshold:
                    return False
        return True

    def neighbours(x, y):
        return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))

    if len(start) != 2 or not all(isinstance(v, int) for v in start):
        raise ValueError('Start must be a pair of grid coordinates')
    start = tuple(start)
    if not traversable(*start):
        return None
    queue = deque([start])
    parent = {start: None}
    distance = {start: 1}
    while queue:
        x, y = queue.popleft()
        adjacent = neighbours(x, y)
        radius = clearance_cells + 1
        if (x, y) not in excluded and distance[(x, y)] >= min_path_cells and any(0 <= x + dx < width and 0 <= y + dy < height
               and rows[y + dy][x + dx] == -1 and hypot(dx, dy) <= radius
               for dy in range(-radius, radius + 1)
               for dx in range(-radius, radius + 1)):
            path = []
            current = (x, y)
            while current is not None:
                path.append(current)
                current = parent[current]
            return list(reversed(path))
        for nx, ny in adjacent:
            if (nx, ny) not in parent and traversable(nx, ny):
                parent[(nx, ny)] = (x, y)
                distance[(nx, ny)] = distance[(x, y)] + 1
                queue.append((nx, ny))
    return None
