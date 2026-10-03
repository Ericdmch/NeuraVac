import math

import pytest

from neuravac_core.config import RobotConfig
from neuravac_core.geometry.kinematics import encoder_delta, integrate
from neuravac_core.models import Pose
from sim.sim2d.base import SimRobotBase
from sim.sim2d.environment import Environment, Obstacle
from sim.sim2d.navigation import plan_path


def test_exact_arc_and_encoder_wrap():
    pose = integrate(Pose(), 1, 1, math.pi / 2)
    assert pose.x == pytest.approx(1)
    assert pose.y == pytest.approx(1)
    assert encoder_delta(3, 65534) == 5
    assert encoder_delta(65534, 3) == -5


async def test_sim_collision_stops_and_seed_reproducibility():
    env = Environment(
        width=3, height=3, start=Pose(x=1, y=1), obstacles=[Obstacle("wall", 1.5, 1, 0.2)]
    )
    base = SimRobotBase(env, RobotConfig(backend="sim"))
    await base.connect()
    await base.set_velocity(0.2, 0)
    for _ in range(30):
        base.step(0.1)
    assert base.pose.x < 1.14
    assert (await base.get_bumper_state()).left
    assert base.velocity == (0, 0)
    assert env.lidar(base.pose, seed=4) == env.lidar(base.pose, seed=4)


def test_sim_route_avoids_inflated_cable_and_replans_moved_obstacle():
    env = Environment.demo()
    path1 = plan_path(env, (0.6, 0.6), (4.7, 2.8), 0.17)
    assert path1
    assert all(env.free(x, y, 0.17) for x, y in path1)
    env.move_obstacle("chair", 3.8, 2.8)
    path2 = plan_path(env, (0.6, 0.6), (4.7, 2.8), 0.17)
    assert path2 and path2 != path1
