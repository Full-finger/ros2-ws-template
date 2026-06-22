"""service 子包：纯业务逻辑（零 rclpy 依赖，pytest 可裸测）。"""
from .obstacle_extractor import ObstacleExtractorService

__all__ = ["ObstacleExtractorService"]
