# ═══════════════════════════════════════════════════════════
#  Model 层：纯 Python 数据结构（零 rclpy 依赖）
# ═══════════════════════════════════════════════════════════
"""本包的纯数据结构（DTO），不依赖 rclpy。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InputData:
    """输入数据。"""
    value: float = 0.0
    timestamp: float = 0.0


@dataclass
class OutputData:
    """输出数据。"""
    result: float = 0.0
    valid: bool = False


@dataclass
class Config:
    """运行时配置。"""
    threshold: float = 0.5
    update_rate: float = 10.0  # Hz
