# ═══ 纯逻辑测试：不需要 ROS2，直接测试 Service 层 ═══
"""ExampleService 的 pytest 测试。

不启动任何 ROS2 节点，只测 service 层纯逻辑。
"""
import pytest

from __PACKAGE_NAME__.model import Config, InputData, InputValidationError
from __PACKAGE_NAME__.service import ExampleService


@pytest.fixture
def svc() -> ExampleService:
    return ExampleService(Config(threshold=0.5, update_rate=10.0))


def test_normal_input(svc: ExampleService) -> None:
    out = svc.process(InputData(value=2.0, timestamp=0.0))
    assert out.result == pytest.approx(1.0)
    assert out.valid is True


def test_zero_input(svc: ExampleService) -> None:
    out = svc.process(InputData(value=0.0, timestamp=0.0))
    assert out.result == pytest.approx(0.0)
    assert out.valid is False


def test_negative_input_raises(svc: ExampleService) -> None:
    with pytest.raises(InputValidationError):
        svc.process(InputData(value=-1.0, timestamp=0.0))


def test_config_update(svc: ExampleService) -> None:
    svc.update_config(Config(threshold=2.0, update_rate=10.0))
    out = svc.process(InputData(value=3.0, timestamp=0.0))
    assert out.result == pytest.approx(6.0)
