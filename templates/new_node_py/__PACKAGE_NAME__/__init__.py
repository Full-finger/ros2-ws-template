"""__PACKAGE_NAME__ — 业务节点（Python 实现）。

三层架构：
  - model/      纯数据结构（零 rclpy）
  - service/    纯业务逻辑（零 rclpy，pytest 可测）
  - controller/ ROS2 适配（唯一 import rclpy）

判定标准：删掉 controller，service 能否脱离 ROS2 用 pytest 裸测？
能 → 合格。
"""
from .model import Config, InputData, OutputData
from .service import ExampleService

__all__ = ["Config", "InputData", "OutputData", "ExampleService"]
