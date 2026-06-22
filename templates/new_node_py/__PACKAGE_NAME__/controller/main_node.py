# ═══════════════════════════════════════════════════════════
#  Controller 层：ROS2 适配
#  - 唯一 import rclpy 的地方
#  - 职责：消息收发、类型转换、异常转日志
#  - 不包含业务逻辑
# ═══════════════════════════════════════════════════════════
"""__PACKAGE_NAME__ 的 ROS2 节点入口。"""
from __future__ import annotations

from rclpy import init, spin, shutdown
from rclpy.node import Node
from std_msgs.msg import Float64

from __PACKAGE_NAME__.model import Config
from __PACKAGE_NAME__.service import ExampleService

import rclpy  # noqa: E402


def main(args=None) -> None:
    init(args=args)
    try:
        spin(MainNode())
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()


class MainNode(Node):
    """订阅示例输入，发布示例输出。"""

    def __init__(self) -> None:
        super().__init__("__PACKAGE_NAME__")

        self.declare_parameter("threshold", 0.5)
        self.declare_parameter("update_rate", 10.0)

        self._svc = ExampleService(self._load_config())

        self._input_sub = self.create_subscription(
            Float64, "~/input/example", self._on_input, 10)
        self._output_pub = self.create_publisher(
            Float64, "~/output/result", 10)

        self.get_logger().info(
            f"节点(Python)已启动 (threshold={self._svc.config.threshold})")

    def _on_input(self, msg: Float64) -> None:
        from __PACKAGE_NAME__.model import InputData, InputValidationError, ProcessingError

        data = InputData(value=msg.data, timestamp=self.get_clock().now().nanoseconds * 1e-9)
        try:
            out = self._svc.process(data)
            ros_msg = Float64()
            ros_msg.data = out.result
            self._output_pub.publish(ros_msg)
        except InputValidationError as e:
            self.get_logger().warning(f"输入校验失败: {e}", throttle_duration_sec=2.0)
        except ProcessingError as e:
            self.get_logger().error(f"处理异常: {e}")

    def _load_config(self) -> Config:
        return Config(
            threshold=self.get_parameter("threshold").value,
            update_rate=self.get_parameter("update_rate").value,
        )
