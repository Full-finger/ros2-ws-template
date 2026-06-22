#!/usr/bin/env python3
"""
scripts/validate_cross.py

校验 plugin.yaml 与 package.xml 之间的一致性:
  1. package.xml <name> == 所在目录名
  2. plugin.yaml depends_on ⊆ package.xml 的全部依赖标签
  3. type=node: runtime.node 顶层 namespace == package.xml <name>
  4. type=messages: plugin.yaml 声明的 msg/srv/action 文件实际存在
  5. type=bringup: subpackages 列出的包在本项目 src/ 中存在

依赖: 仅 stdlib (xml.etree.ElementTree) + pyyaml。
退出码: 0 全部通过, 1 有错误。
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

# package.xml 中所有"依赖类"标签
DEP_TAGS = ("depend", "build_depend", "exec_depend",
            "build_export_depend", "test_depend")


def parse_package_xml(pkg_dir: Path) -> dict | None:
    """用 stdlib xml.etree 解析 package.xml。返回 None 表示文件不存在。"""
    xml_path = pkg_dir / "package.xml"
    if not xml_path.exists():
        return None
    tree = ET.parse(str(xml_path))
    r = tree.getroot()

    def text(tag):
        el = r.find(tag)
        return el.text.strip() if el is not None and el.text else ""

    deps = set()
    for tag in DEP_TAGS:
        for el in r.findall(tag):
            if el.text:
                deps.add(el.text.strip())
    return {"name": text("name"), "version": text("version"), "deps": deps}


def parse_plugin_yaml(pkg_dir: Path) -> dict | None:
    p = pkg_dir / "plugin.yaml"
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_node_namespace(plugin: dict, pkg_name: str, pkg_dir: Path) -> list:
    node_class = plugin.get("runtime", {}).get("node", "")
    if not node_class:
        return []
    # C++: "foo::controller::MainNode"  →  顶层 = foo
    # Python: "foo.controller.main_node:MainNode"  →  顶层 = foo
    entry = node_class.split(":")[0]  # 去掉 py 的 :Class
    top_ns = entry.replace("::", ".").split(".")[0]
    if top_ns != pkg_name:
        return [f"  ✗ {pkg_dir.name}: runtime.node 顶层 namespace "
                f"'{top_ns}' != package.xml name '{pkg_name}'"]
    return []


def check_interfaces_exist(plugin: dict, pkg_dir: Path) -> list:
    errs = []
    for iface_type in ("msg", "srv", "action"):
        iface_dir = pkg_dir / iface_type
        for fname in plugin.get("interfaces", {}).get(iface_type, []) or []:
            if not (iface_dir / fname).exists():
                errs.append(f"  ✗ {pkg_dir.name}: 声明了 {iface_type}/{fname} 但文件不存在")
    return errs


def check_depends_on(plugin: dict, pkg_xml: dict, pkg_dir: Path) -> list:
    declared = set(plugin.get("depends_on", []) or [])
    declared.discard(pkg_xml["name"])  # 自身不算
    missing = declared - pkg_xml["deps"]
    if missing:
        return [f"  ✗ {pkg_dir.name}: plugin.yaml depends_on 含 {sorted(missing)} "
                f"但 package.xml 缺少对应 <depend>/<exec_depend> 等"]
    return []


def check_depends_on_reverse(plugin: dict, pkg_xml: dict, pkg_dir: Path,
                             all_pkg_names: set) -> list:
    """反向检查：package.xml 声明的【本项目内部】包依赖，
    应出现在 plugin.yaml 的 depends_on（仅 node/library 类型）。
    bringup 的 subpackages 可能只列直接启动的包，传递依赖允许不声明。"""
    internal = {d for d in pkg_xml["deps"]
                if d in all_pkg_names and d != pkg_xml["name"]}
    if not internal:
        return []
    declared = set(plugin.get("depends_on", []) or [])
    missing = internal - declared
    if missing:
        return [f"  ✗ {pkg_dir.name}: package.xml 依赖本项目包 {sorted(missing)} "
                f"但 plugin.yaml depends_on 未声明"]
    return []


def check_bringup_subpackages(plugin: dict, pkg_dir: Path) -> list:
    errs = []
    for sub in plugin.get("subpackages", []) or []:
        if not (SRC / sub).is_dir():
            errs.append(f"  ✗ {pkg_dir.name}: subpackages 含 '{sub}' 但 src/{sub} 不存在")
    return errs


def main() -> int:
    if not SRC.exists():
        print(f"错误: {SRC} 不存在", file=sys.stderr)
        return 1

    all_errors: list = []
    count = 0

    print("== plugin.yaml ↔ package.xml 交叉校验 ==")
    # 先收集所有包名，供反向依赖检查
    all_pkg_names = {p.name for p in SRC.iterdir()
                     if p.is_dir() and (p / "plugin.yaml").exists()}
    for pkg_dir in sorted(p for p in SRC.iterdir() if p.is_dir()):
        plugin = parse_plugin_yaml(pkg_dir)
        if plugin is None:
            continue
        pkg_xml = parse_package_xml(pkg_dir)
        if pkg_xml is None:
            all_errors.append(f"  ✗ {pkg_dir.name}: 缺少 package.xml")
            continue

        count += 1
        pkg_type = plugin.get("type", "unknown")

        # 目录名 == package.xml name
        if pkg_xml["name"] and pkg_xml["name"] != pkg_dir.name:
            all_errors.append(f"  ✗ {pkg_dir.name}: package.xml name "
                              f"'{pkg_xml['name']}' != 目录名 '{pkg_dir.name}'")

        if pkg_type == "node":
            all_errors.extend(check_node_namespace(plugin, pkg_xml["name"], pkg_dir))
        if pkg_type == "messages":
            all_errors.extend(check_interfaces_exist(plugin, pkg_dir))
        if pkg_type == "bringup":
            all_errors.extend(check_bringup_subpackages(plugin, pkg_dir))

        all_errors.extend(check_depends_on(plugin, pkg_xml, pkg_dir))
        if pkg_type in ("node", "library"):
            all_errors.extend(check_depends_on_reverse(
                plugin, pkg_xml, pkg_dir, all_pkg_names))

        print(f"  {pkg_dir.name:25s} type={pkg_type:10s} ✓")

    print(f"\n检查了 {count} 个包")
    if all_errors:
        print(f"\n发现 {len(all_errors)} 个问题:")
        for e in all_errors:
            print(e)
        return 1
    print("✓ 所有一致性检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
