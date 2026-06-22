# ═══════════════════════════════════════════════════════════
#  Service 层：纯业务逻辑（零 rclpy 依赖）
#
#  这一层不 import 任何 rclpy / *_msgs，可脱离 ROS2 用 pytest 裸测。
#  输入 Model 类型，输出 Model 类型。
# ═══════════════════════════════════════════════════════════
"""示例 service：纯逻辑，输入输出都是 model 类型。"""
from __future__ import annotations

from __PACKAGE_NAME__.model import Config, InputData, OutputData


class ExampleService:
    """示例业务逻辑。"""

    def __init__(self, config: Config) -> None:
        self._config = config

    def process(self, data: InputData) -> OutputData:
        if data.value < 0:
            from __PACKAGE_NAME__.model import InputValidationError
            raise InputValidationError("输入值不能为负")

        out = OutputData()
        out.result = data.value * self._config.threshold
        out.valid = out.result > 0.01
        return out

    def update_config(self, config: Config) -> None:
        self._config = config

    @property
    def config(self) -> Config:
        return self._config
