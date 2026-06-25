"""model 子包：纯数据结构与异常（零 rclpy 依赖）。"""

from .errors import PerceptionError
from .types import Config, LaserPoint, ObstacleProto

__all__ = ["Config", "LaserPoint", "ObstacleProto", "PerceptionError"]
