"""robot_perception_py — 感知节点（Python 实现）。

三层架构：
  - model/      纯数据结构（零 rclpy）
  - service/    纯业务逻辑（零 rclpy，pytest 可测）
  - controller/ ROS2 适配（唯一 import rclpy）

判定标准：删掉 controller，service 能否脱离 ROS2 用 pytest 裸测？
能 → 合格。
"""
from .model import Config, LaserPoint, ObstacleProto, PerceptionError
from .service import ObstacleExtractorService

__all__ = [
    "Config",
    "LaserPoint",
    "ObstacleProto",
    "PerceptionError",
    "ObstacleExtractorService",
]
