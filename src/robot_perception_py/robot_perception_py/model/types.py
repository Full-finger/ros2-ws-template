# ═══════════════════════════════════════════════════════════
#  Model 层：感知包的纯 Python 数据结构（零 rclpy 依赖）
# ═══════════════════════════════════════════════════════════
"""感知包的纯数据结构（DTO），不依赖 rclpy。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LaserPoint:
    """单个激光点（极坐标）。"""
    range: float = 0.0
    angle: float = 0.0


@dataclass
class ObstacleProto:
    """提取后的障碍物（笛卡尔）。"""
    x: float = 0.0
    y: float = 0.0
    radius: float = 0.0   # 包络半径
    count: int = 0        # 构成点数


@dataclass
class Config:
    """运行时配置。"""
    max_range: float = 5.0      # m，超过则丢弃
    min_range: float = 0.05     # m，小于则丢弃（噪点）
    min_points: int = 1         # 至少多少个有效点才算障碍物
