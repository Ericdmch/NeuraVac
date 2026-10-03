"""Grid A* ONLY for CI simulation; production delegates path planning to Nav2."""

import heapq
import math

from sim.sim2d.environment import Environment


def plan_path(
    env: Environment,
    start: tuple[float, float],
    goal: tuple[float, float],
    radius: float,
    resolution: float = 0.1,
) -> list[tuple[float, float]]:
    def cell(p: tuple[float, float]) -> tuple[int, int]:
        return round(p[0] / resolution), round(p[1] / resolution)

    def point(c: tuple[int, int]) -> tuple[float, float]:
        return c[0] * resolution, c[1] * resolution

    source, target = cell(start), cell(goal)
    if not env.free(*goal, radius):
        return []
    frontier = [(0.0, source)]
    parent: dict[tuple[int, int], tuple[int, int]] = {}
    cost = {source: 0.0}
    while frontier:
        _, current = heapq.heappop(frontier)
        if current == target:
            cells = [current]
            while current != source:
                current = parent[current]
                cells.append(current)
            route = [point(c) for c in reversed(cells)]
            route[0], route[-1] = start, goal
            return route
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            nxt = current[0] + dx, current[1] + dy
            if not env.free(*point(nxt), radius):
                continue
            # No diagonal corner-cutting; validate swept segment midpoint too.
            if (
                dx
                and dy
                and (
                    not env.free(*point((current[0] + dx, current[1])), radius)
                    or not env.free(*point((current[0], current[1] + dy)), radius)
                )
            ):
                continue
            tentative = cost[current] + math.hypot(dx, dy)
            if tentative >= cost.get(nxt, math.inf):
                continue
            cost[nxt], parent[nxt] = tentative, current
            heapq.heappush(
                frontier, (tentative + math.hypot(nxt[0] - target[0], nxt[1] - target[1]), nxt)
            )
    return []
