#!/usr/bin/env python3
"""
scripts/validate_layers.py

机器化校验三层架构的边界（docs/conventions.md 的硬性约定）：

  C++ 包：
    - model 层：零 ROS2 依赖
    - service 层：零 ROS2 依赖（仅 STL + model + robot_common）
    - library（且 no_ros2_dependency: true）：零 ROS2 依赖
    - controller 层：任意（唯一允许接触 ROS2）

  Python 包（plugin.yaml: language: python）：
    - model/   子包：禁止 import rclpy / rclpy.* / <pkg>_msgs
    - service/ 子包：禁止 import rclpy / rclpy.* / <pkg>_msgs
    - controller/ 是唯一允许接触 rclpy 的层

两道互补检查：
  1. include/import 边界 — 直接扫描 #include / import 语句
  2. 符号级边界（补漏）— 扫描代码体里实际使用的 ROS2 符号 / controller 业务数学
     即便没直接 #include，靠传递 include 也能偷偷用 rclcpp::；符号扫描防漏网。
     对 AI 辅助编码：宁可误杀，尽量少漏报（误报改名即可，漏报是上线 bug）。

依赖：pyyaml。退出码：0 通过，1 有违规。
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

# ═══ include/import 级正则 ═══

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

# ═══ 符号级正则（补 include/import 检查的盲区）═══

# service/model 里出现的 ROS2 符号（哪怕没直接 include，传递 include 也能用上）。
# C++ 形如 rclcpp::Node、nav_msgs::msg::Odometry、rcl_interfaces::ParameterType
ROS2_SYMBOL_CPP_RE = re.compile(
    r"\b(rclcpp|rcutils|rcl_interfaces|tf2|pluginlib)::"
    r"|::(msg|srv|action)::"
    r"|\b[a-z_]+_(msgs|srvs|actions)::"
)
# Python 形如 rclpy.create_node(...) 的属性访问
ROS2_SYMBOL_PY_RE = re.compile(r"\brclpy\.")

# controller 层禁止业务数学：几何/物理运算属 service，controller 只做类型转换。
# 白名单：abs/min/max/round/clamp 属数据清理/范围处理，转换常用，不拦。
# 拦的是 sin/cos/atan2/hypot/sqrt 这类「真正的几何/物理计算」。
BIZ_MATH_CPP_RE = re.compile(
    r"\bstd::(sin|cos|tan|atan2|asin|acos|atan|hypot|sqrt|fmod|pow|exp|log)\b"
)
BIZ_MATH_PY_RE = re.compile(
    r"\bmath\.(sin|cos|tan|atan2|asin|acos|atan|hypot|sqrt|fmod|pow|exp|log)\b"
)


# ═══ include/import 级扫描 ═══


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


# ═══ 符号级扫描 ═══


def symbols_in_file(path: Path, language: str) -> list[tuple[str, str]]:
    """返回 [(行号, 命中片段)]：service/model 命中 ROS2 符号。"""
    if language == "python":
        sym_re = ROS2_SYMBOL_PY_RE
    else:
        sym_re = ROS2_SYMBOL_CPP_RE
    hits = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        m = sym_re.search(line)
        if m:
            hits.append((str(i), m.group(0)))
    return hits


def biz_math_in_file(path: Path, language: str) -> list[tuple[str, str]]:
    """返回 [(行号, 命中片段)]：controller 命中业务数学函数。"""
    math_re = BIZ_MATH_PY_RE if language == "python" else BIZ_MATH_CPP_RE
    hits = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        m = math_re.search(line)
        if m:
            hits.append((str(i), m.group(0)))
    return hits


# ═══ 目录级扫描调度 ═══


def check_dir(
    d: Path, pkg: str, layer: str, violations: list, language: str = "cpp"
) -> int:
    """检查某目录下所有源文件的 ROS2 include/import 依赖。返回扫描文件数。"""
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


def check_symbols_dir(
    d: Path, pkg: str, layer: str, violations: list, language: str = "cpp"
) -> None:
    """符号级扫描：service/model 查 ROS2 符号越界；controller 查业务数学泄漏。"""
    if not d.exists():
        return
    suffixes = (".py",) if language == "python" else (".hpp", ".cpp", ".h", ".cc")
    for f in sorted(d.rglob("*")):
        if f.suffix not in suffixes:
            continue
        rel = f.relative_to(ROOT)
        if layer in ("model", "service", "library"):
            for lineno, hit in symbols_in_file(f, language):
                violations.append(
                    f"  ✗ {pkg}/{layer}: {rel}:L{lineno} 出现 ROS2 符号 '{hit}' "
                    f"（即便未直接 include，也不得使用）"
                )
        elif layer == "controller":
            for lineno, hit in biz_math_in_file(f, language):
                violations.append(
                    f"  ✗ {pkg}/{layer}: {rel}:L{lineno} 出现业务数学 '{hit}' "
                    f"（几何/物理运算应下沉到 service 或 robot_common）"
                )


def check_cpp_node(pkg_dir: Path, pkg: str, violations: list) -> int:
    """C++ node 包：include 边界（model/service）+ 符号边界（全三层）。"""
    inc = pkg_dir / "include" / pkg
    # include 级
    scanned = check_dir(inc / "model", pkg, "model", violations)
    scanned += check_dir(inc / "service", pkg, "service", violations)
    scanned += check_dir(pkg_dir / "src" / "service", pkg, "service(src)", violations)
    # 符号级：service/model 查 ROS2 符号；controller 查业务数学
    check_symbols_dir(inc / "model", pkg, "model", violations)
    check_symbols_dir(inc / "service", pkg, "service", violations)
    check_symbols_dir(inc / "controller", pkg, "controller", violations)
    return scanned


def check_py_node(pkg_dir: Path, pkg: str, violations: list) -> int:
    """Python node 包：import 边界 + 符号边界。

    ROS2 ament_python 包结构：<pkg_dir>/<python_pkg>/model, /service, /controller
    （包名带 _py 后缀时，Python 模块名 = 目录名）
    """
    python_pkg = pkg  # 如 robot_perception_py
    src_dir = pkg_dir / python_pkg
    scanned = check_dir(src_dir / "model", pkg, "model", violations, "python")
    scanned += check_dir(src_dir / "service", pkg, "service", violations, "python")
    check_symbols_dir(src_dir / "model", pkg, "model", violations, "python")
    check_symbols_dir(src_dir / "service", pkg, "service", violations, "python")
    check_symbols_dir(src_dir / "controller", pkg, "controller", violations, "python")
    return scanned


def check_cpp_library(pkg_dir: Path, pkg: str, data: dict, violations: list) -> int:
    """C++ library 包：no_ros2_dependency=true 时全库扫（include + 符号）。"""
    no_ros2 = (data.get("exposes", {}) or {}).get("no_ros2_dependency", False)
    if not no_ros2:
        return 0
    inc = pkg_dir / "include"
    scanned = check_dir(inc, pkg, "library", violations)
    scanned += check_dir(pkg_dir / "src", pkg, "library(src)", violations)
    check_symbols_dir(inc, pkg, "library", violations)
    check_symbols_dir(pkg_dir / "src", pkg, "library", violations)
    return scanned


def main() -> int:
    if not SRC.exists():
        print(f"错误: {SRC} 不存在", file=sys.stderr)
        return 1

    print("== 分层边界校验（include/import + 符号级）==")
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
                note = f"py model+service+controller ({n} 文件)"
            else:
                n = check_cpp_node(pkg_dir, pkg, violations)
                note = f"cpp 全三层符号 + model/service include ({n} 文件)"
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
                    "全库 include+符号 (no_ros2_dependency=true)"
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
    print(f"\n✓ 分层边界合法（扫描 {scanned} 个源文件，零越界）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
