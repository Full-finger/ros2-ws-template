# ═══════════════════════════════════════════════════════════
#  Service 层：障碍物提取（纯 Python 逻辑，零 rclpy 依赖）
#
#  策略（求质心法，和 C++ 示范包保持一致）：
#   1. 极坐标 → 笛卡尔，丢弃越界/非法点
#   2. 求所有有效点的质心，作为单一障碍物中心
#   3. 半径 = 有效点到质心的最大距离
#   4. 有效点数 >= min_points 才输出
#
#  这一层不 import 任何 rclpy / *_msgs，可脱离 ROS2 用 pytest 裸测。
# ═══════════════════════════════════════════════════════════
"""障碍物提取 service：纯逻辑，输入输出都是 model 类型。"""
from __future__ import annotations

import math
from typing import List

from robot_perception_py.model import Config, LaserPoint, ObstacleProto


class ObstacleExtractorService:
    """从激光点集提取障碍物（质心法）。"""

    def __init__(self, config: Config) -> None:
        self._config = config

    def extract(self, points: List[LaserPoint]) -> List[ObstacleProto]:
        # 第一遍：过滤无效点，累计质心坐标和
        sum_x = 0.0
        sum_y = 0.0
        count = 0
        for p in points:
            if not self._is_valid(p.range):
                continue
            sum_x += p.range * math.cos(p.angle)
            sum_y += p.range * math.sin(p.angle)
            count += 1
        if count < self._config.min_points:
            return []

        # 质心
        cx = sum_x / count
        cy = sum_y / count

        # 第二遍：到质心的最大距离（包络半径）
        radius = 0.0
        for p in points:
            if not self._is_valid(p.range):
                continue
            dx = p.range * math.cos(p.angle) - cx
            dy = p.range * math.sin(p.angle) - cy
            radius = max(radius, math.hypot(dx, dy))

        return [ObstacleProto(x=cx, y=cy, radius=radius, count=count)]

    def update_config(self, config: Config) -> None:
        self._config = config

    @property
    def config(self) -> Config:
        return self._config

    def _is_valid(self, value: float) -> bool:
        return (math.isfinite(value)
                and value >= self._config.min_range
                and value <= self._config.max_range)
