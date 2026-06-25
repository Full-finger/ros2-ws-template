#!/usr/bin/env python3
"""
scripts/validate_layers.py

机器化校验三层架构的 include 边界（docs/conventions.md 的硬性约定）：

  C++ 包：
    - model 层：零 ROS2 依赖
    - service 层：零 ROS2 依赖（仅 STL + model + robot_common）
    - library（且 no_ros2_dependency: true）：零 ROS2 依赖
    - controller 层：任意（唯一允许接触 ROS2）

  Python 包（plugin.yaml: language: python）：
    - model/   子包：禁止 import rclpy / rclpy.* / <pkg>_msgs
    - service/ 子包：禁止 import rclpy / rclpy.* / <pkg>_msgs
    - controller/ 是唯一允许接触 rclpy 的层
    判定：扫描 import 语句（含 from X import / import X），命中 ROS2 标记即违规。

依赖：pyyaml。退出码：0 通过，1 有违规。
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

# C++：ROS2 client lib 的顶层包标记。命中任一即视为 ROS2 依赖。
# _msgs/ 覆盖 *_msgs（含 action_msgs），_srvs/ 覆盖 *_srvs。
ROS2_INCLUDE_RE = re.compile(
    r"(rclcpp|rclpy|rcl/|_msgs/|_srvs/|"
    r"tf2|rosidl_|pluginlib|message_filters|"
    r"image_transport|class_loader|bond|"
    r"actionlib|lifecycle)"
)

# Python：匹配 import 语句里的 ROS2 模块。
# 形如：  import rclpy        from rclpy.node import Node
#         import robot_msgs   from robot_msgs.msg import Obstacle
ROS2_PY_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+(rclpy|rclpy\.[\w.]+|[a-z_]+_msgs(?:\.[\w.]+)?)\s+import"
    r"|import\s+(rclpy|rclpy\.[\w.]+|[a-z_]+_msgs(?:\.[\w.]+)?))"
)


def ros2_includes_in_file(path: Path) -> list:
    """返回文件中所有命中 ROS2 标记的 include 行（C++）。"""
    hits = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("#include") and ROS2_INCLUDE_RE.search(s):
            hits.append(s)
    return hits


def ros2_imports_in_file(path: Path) -> list:
    """返回文件中所有命中 ROS2 import 的行（Python）。"""
    hits = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if ROS2_PY_IMPORT_RE.match(line):
            hits.append(line.strip())
    return hits


def check_dir(
    d: Path, pkg: str, layer: str, violations: list, language: str = "cpp"
) -> int:
    """检查某目录下所有源文件的 ROS2 依赖。返回扫描文件数。"""
    if not d.exists():
        return 0
    suffixes = (".py",) if language == "python" else (".hpp", ".cpp", ".h", ".cc")
    detector = ros2_imports_in_file if language == "python" else ros2_includes_in_file
    count = 0
    for f in sorted(d.rglob("*")):
        if f.suffix not in suffixes:
            continue
        count += 1
        for hit in detector(f):
            violations.append(
                f"  ✗ {pkg}/{layer}: {f.relative_to(ROOT)} 命中 ROS2 "
                f"{'import' if language == 'python' else 'include'}: {hit}"
            )
    return count


def check_cpp_node(pkg_dir: Path, pkg: str, violations: list) -> int:
    """C++ node 包：扫 include/model + include/service + src/service。"""
    inc = pkg_dir / "include" / pkg
    scanned = check_dir(inc / "model", pkg, "model", violations)
    scanned += check_dir(inc / "service", pkg, "service", violations)
    scanned += check_dir(pkg_dir / "src" / "service", pkg, "service(src)", violations)
    return scanned


def check_py_node(pkg_dir: Path, pkg: str, violations: list) -> int:
    """Python node 包：扫 <pkg>/<pkg>/model + <pkg>/<pkg>/service。

    ROS2 ament_python 包结构：<pkg_dir>/<python_pkg>/model, /service, /controller
    （包名带 _py 后缀时，Python 模块名 = 目录名）
    """
    python_pkg = pkg  # 如 robot_perception_py
    src_dir = pkg_dir / python_pkg
    scanned = check_dir(src_dir / "model", pkg, "model", violations, "python")
    scanned += check_dir(src_dir / "service", pkg, "service", violations, "python")
    return scanned


def check_cpp_library(pkg_dir: Path, pkg: str, data: dict, violations: list) -> int:
    """C++ library 包：no_ros2_dependency=true 时全库扫。"""
    no_ros2 = (data.get("exposes", {}) or {}).get("no_ros2_dependency", False)
    if not no_ros2:
        return 0
    inc = pkg_dir / "include"
    scanned = check_dir(inc, pkg, "library", violations)
    scanned += check_dir(pkg_dir / "src", pkg, "library(src)", violations)
    return scanned


def main() -> int:
    if not SRC.exists():
        print(f"错误: {SRC} 不存在", file=sys.stderr)
        return 1

    print("== 分层 import 边界校验 ==")
    violations = []
    scanned = 0

    for pkg_dir in sorted(p for p in SRC.iterdir() if p.is_dir()):
        pf = pkg_dir / "plugin.yaml"
        if not pf.exists():
            continue
        data = yaml.safe_load(pf.read_text(encoding="utf-8"))
        pkg = pkg_dir.name
        ptype = data.get("type", "unknown")
        language = data.get("language", "cpp")  # 默认 cpp（向后兼容）

        n = 0  # 本包扫描的源文件数（note 显示单包计数）
        if ptype == "node":
            if language == "python":
                n = check_py_node(pkg_dir, pkg, violations)
                note = f"py model+service 检查 ({n} 文件)"
            else:
                n = check_cpp_node(pkg_dir, pkg, violations)
                note = f"cpp model+service 检查 ({n} 文件)"
        elif ptype == "library":
            if language == "python":
                # Python library 包暂不强制（少见，按需扩展）
                note = "跳过 (Python library)"
            else:
                n = check_cpp_library(pkg_dir, pkg, data, violations)
                no_ros2 = (data.get("exposes", {}) or {}).get(
                    "no_ros2_dependency", False
                )
                note = (
                    "全库检查 (no_ros2_dependency=true)"
                    if no_ros2
                    else "跳过 (no_ros2_dependency=false)"
                )
        else:
            note = "跳过 (无源码)"
        scanned += n
        print(f"  {pkg:20s} type={ptype:10s} lang={language:6s} {note}")

    if violations:
        print(f"\n发现 {len(violations)} 处分层违规：")
        for v in violations:
            print(v)
        return 1
    print(f"\n✓ 分层边界合法（扫描 {scanned} 个源文件，零 ROS2 越界）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
