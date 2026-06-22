"""model 子包：纯数据结构与异常（零 rclpy 依赖）。"""
from .errors import InputValidationError, ProcessingError
from .types import Config, InputData, OutputData

__all__ = ["Config", "InputData", "OutputData",
           "InputValidationError", "ProcessingError"]
