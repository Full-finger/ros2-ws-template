# ═══ 障碍物提取测试（纯逻辑，不依赖 ROS2） ═══
"""ObstacleExtractorService 的 pytest 测试。

不启动任何 ROS2 节点，只测 service 层纯逻辑。
"""
import math

import pytest

from robot_perception_py.model import Config, LaserPoint
from robot_perception_py.service import ObstacleExtractorService


@pytest.fixture
def svc() -> ObstacleExtractorService:
    return ObstacleExtractorService(Config(max_range=5.0, min_range=0.05, min_points=1))


def test_empty_input_returns_empty(svc: ObstacleExtractorService) -> None:
    assert svc.extract([]) == []


def test_single_point_at_center(svc: ObstacleExtractorService) -> None:
    result = svc.extract([LaserPoint(range=1.0, angle=0.0)])  # (1, 0)
    assert len(result) == 1
    assert result[0].x == pytest.approx(1.0)
    assert result[0].y == pytest.approx(0.0)
    assert result[0].radius == pytest.approx(0.0)  # 单点，到质心距离为 0
    assert result[0].count == 1


def test_multiple_points_centroid(svc: ObstacleExtractorService) -> None:
    # 正前方 1m 和正左方 1m，质心 (0.5, 0.5)
    result = svc.extract(
        [
            LaserPoint(range=1.0, angle=0.0),  # (1, 0)
            LaserPoint(range=1.0, angle=math.pi / 2),  # (0, 1)
        ]
    )
    assert len(result) == 1
    assert result[0].x == pytest.approx(0.5)
    assert result[0].y == pytest.approx(0.5)
    assert result[0].count == 2


def test_out_of_range_points_dropped(svc: ObstacleExtractorService) -> None:
    result = svc.extract(
        [
            LaserPoint(range=10.0, angle=0.0),  # 超 max_range
            LaserPoint(range=0.01, angle=0.0),  # 小于 min_range
        ]
    )
    assert result == []


def test_min_points_filter() -> None:
    svc = ObstacleExtractorService(Config(max_range=5.0, min_range=0.05, min_points=3))
    p = LaserPoint(range=1.0, angle=0.0)
    assert svc.extract([p, p]) == []  # 只有 2 点 < min_points=3
