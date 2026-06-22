#!/usr/bin/env python3
"""
scripts/validate_layers.py

机器化校验三层架构的 include 边界（docs/conventions.md 的硬性约定）：
  - model 层：零 ROS2 依赖
  - service 层：零 ROS2 依赖（仅 STL + model + robot_common）
  - library（且 no_ros2_dependency: true）：零 ROS2 依赖
  - controller 层：任意（唯一允许接触 ROS2）

判定：#include 路径命中 rclcpp / rcl/ / _msgs/ / tf2/ / rosidl_ 即视为 ROS2 依赖。
依赖：pyyaml。退出码：0 通过，1 有违规。
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

ROS2_INCLUDE_RE = re.compile(r'(rclcpp|rcl/|_msgs/|tf2/|rosidl_)')


def ros2_includes_in_file(path: Path) -> list:
    """返回文件中所有命中 ROS2 标记的 include 行。"""
    hits = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("#include") and ROS2_INCLUDE_RE.search(s):
            hits.append(s)
    return hits


def check_dir(d: Path, pkg: str, layer: str, violations: list) -> int:
    """检查某目录下所有 .hpp/.cpp 的 ROS2 include。返回扫描文件数。"""
    if not d.exists():
        return 0
    count = 0
    for f in sorted(d.rglob("*")):
        if f.suffix not in (".hpp", ".cpp", ".h", ".cc"):
            continue
        count += 1
        for hit in ros2_includes_in_file(f):
            violations.append(
                f"  ✗ {pkg}/{layer}: {f.relative_to(ROOT)} 命中 ROS2 include: {hit}")
    return count


def main() -> int:
    if not SRC.exists():
        print(f"错误: {SRC} 不存在", file=sys.stderr)
        return 1

    print("== 分层 include 边界校验 ==")
    violations = []
    scanned = 0

    for pkg_dir in sorted(p for p in SRC.iterdir() if p.is_dir()):
        pf = pkg_dir / "plugin.yaml"
        if not pf.exists():
            continue
        data = yaml.safe_load(pf.read_text(encoding="utf-8"))
        pkg = pkg_dir.name
        ptype = data.get("type", "unknown")
        inc = pkg_dir / "include" / pkg

        if ptype == "node":
            scanned += check_dir(inc / "model", pkg, "model", violations)
            scanned += check_dir(inc / "service", pkg, "service", violations)
            note = f"model+service 检查 ({scanned} 文件)"
        elif ptype == "library":
            no_ros2 = (data.get("exposes", {}) or {}).get(
                "no_ros2_dependency", False)
            if no_ros2:
                scanned += check_dir(inc, pkg, "library", violations)
                note = "全库检查 (no_ros2_dependency=true)"
            else:
                note = "跳过 (no_ros2_dependency=false)"
        else:
            note = "跳过 (无 C++ 源码)"
        print(f"  {pkg:20s} type={ptype:10s} {note}")

    if violations:
        print(f"\n发现 {len(violations)} 处分层违规：")
        for v in violations:
            print(v)
        return 1
    print(f"\n✓ 分层边界合法（扫描 {scanned} 个源文件，零 ROS2 越界）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
