# ═══════════════════════════════════════════════════════════
#  Controller 层：ROS2 适配
#  - 订阅 LaserScan
#  - 调 ObstacleExtractorService 提取障碍物
#  - model 障碍物 → robot_msgs/ObstacleArray 发布
#
#  唯一 import rclpy / robot_msgs 的地方。业务逻辑全在 service。
# ═══════════════════════════════════════════════════════════
"""robot_perception_py 的 ROS2 节点入口。"""
from __future__ import annotations

import math

from rclpy import init, spin, shutdown
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

from robot_msgs.msg import Obstacle, ObstacleArray

from robot_perception_py.model import Config
from robot_perception_py.service import ObstacleExtractorService

import rclpy  # noqa: E402 (主入口放一起便于阅读)


def main(args=None) -> None:
    init(args=args)
    try:
        spin(MainNode())
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()


class MainNode(Node):
    """订阅 LaserScan，发布 ObstacleArray。"""

    def __init__(self) -> None:
        super().__init__("robot_perception")

        self.declare_parameter("max_range", 5.0)
        self.declare_parameter("min_range", 0.05)
        self.declare_parameter("min_points", 1)

        self._svc = ObstacleExtractorService(self._load_config())

        self._scan_sub = self.create_subscription(
            LaserScan, "~/input/scan", self._on_scan, 10)
        self._obstacles_pub = self.create_publisher(
            ObstacleArray, "~/output/obstacles", 10)

        self.get_logger().info(
            f"感知节点(Python)已启动 (min_points="
            f"{self._svc.config.min_points})")

    def _on_scan(self, msg: LaserScan) -> None:
        from robot_perception_py.model import LaserPoint

        # ROS LaserScan → model::LaserPoint
        points = [
            LaserPoint(
                range=msg.ranges[i],
                angle=msg.angle_min + msg.angle_increment * i,
            )
            for i in range(len(msg.ranges))
        ]

        # 提取质心
        protos = self._svc.extract(points)

        # model::ObstacleProto → robot_msgs/ObstacleArray
        out = ObstacleArray()
        out.header = msg.header
        for pr in protos:
            ob = Obstacle()
            ob.center.x = pr.x
            ob.center.y = pr.y
            ob.center.z = 0.0
            ob.radius = pr.radius
            ob.confidence = min(100, pr.count * 10)  # 点数 → 置信度
            out.obstacles.append(ob)
        self._obstacles_pub.publish(out)

        self.get_logger().debug(f"提取出 {len(protos)} 个障碍物")

    def _load_config(self) -> Config:
        return Config(
            max_range=self.get_parameter("max_range").value,
            min_range=self.get_parameter("min_range").value,
            min_points=self.get_parameter("min_points").value,
        )
