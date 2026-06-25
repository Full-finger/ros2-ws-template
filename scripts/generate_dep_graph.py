#!/usr/bin/env python3
"""
scripts/generate_dep_graph.py

从所有 plugin.yaml 的 type 和 depends_on 生成 Graphviz dot，
并按 type 上色。输出到 stdout（重定向到 docs/dependency_graph.dot）。

依赖: pyyaml。
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

COLORS = {
    "messages": "#c8e6c9",  # 绿
    "library": "#bbdefb",  # 蓝
    "node": "#fff9c4",  # 黄
    "bringup": "#f8bbd0",  # 粉
}


def main() -> int:
    print("digraph G {")
    print("  rankdir=LR;")
    print('  node [shape=box, style="rounded,filled", ' 'fontname="Helvetica"];')
    print()

    pkgs = {}
    for pf in sorted(SRC.glob("*/plugin.yaml")):
        data = yaml.safe_load(pf.read_text(encoding="utf-8"))
        name = pf.parent.name
        pkgs[name] = data
        ptype = data.get("type", "unknown")
        color = COLORS.get(ptype, "#eeeeee")
        print(f'  "{name}" [fillcolor="{color}", label="{name}\\n({ptype})"];')
    print()

    for name, data in pkgs.items():
        deps = list(data.get("depends_on", []) or [])
        # bringup 的 subpackages 也画成依赖边
        if data.get("type") == "bringup":
            deps.extend(data.get("subpackages", []) or [])
        for dep in deps:
            if dep in pkgs:
                print(f'  "{dep}" -> "{name}";')
    print("}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
