#!/usr/bin/env python3
"""
scripts/validate_deps.py

校验包依赖链的完整性与合理性:
  1. 无循环依赖（拓扑排序可成）
  2. depends_on 引用的包在 src/ 中存在
  3. 分层约束（编译时依赖方向只能从上往下）:
       messages  → 最底层
       library   → 只能依赖 library/messages
       node      → 可依赖 library/messages/node
       bringup   → 可依赖任何类型
     禁止: messages 依赖任何东西; library 依赖 node/bringup; node 依赖 bringup

依赖: pyyaml。退出码: 0 通过, 1 有错误。
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

# 类型层级: 数值越小越底层。允许"依赖层级 <= 自身层级"。
TYPE_RANK = {"messages": 0, "library": 1, "node": 2, "bringup": 3}


def load_packages() -> dict:
    pkgs = {}
    for d in sorted(p for p in SRC.iterdir() if p.is_dir()):
        pf = d / "plugin.yaml"
        if not pf.exists():
            continue
        data = yaml.safe_load(pf.read_text(encoding="utf-8"))
        deps = list(data.get("depends_on", []) or [])
        # bringup 的 subpackages 也是依赖边（启动它们）
        if data.get("type") == "bringup":
            deps.extend(data.get("subpackages", []) or [])
        pkgs[d.name] = {
            "type": data.get("type", "unknown"),
            "depends_on": deps,
            "dir": d,
        }
    return pkgs


def detect_cycles(pkgs: dict) -> list:
    """返回所有环（每个环是包名列表）。"""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in pkgs}
    cycles = []

    def dfs(node, stack):
        color[node] = GRAY
        stack.append(node)
        for dep in pkgs[node]["depends_on"]:
            if dep not in pkgs:
                continue  # 引用缺失，由别的检查处理
            if color[dep] == GRAY:
                idx = stack.index(dep)
                cycles.append(stack[idx:] + [dep])
            elif color[dep] == WHITE:
                dfs(dep, stack)
        stack.pop()
        color[node] = BLACK

    for n in pkgs:
        if color[n] == WHITE:
            dfs(n, [])
    return cycles


def check_layering(pkgs: dict) -> list:
    errs = []
    for name, info in pkgs.items():
        self_rank = TYPE_RANK.get(info["type"], 99)
        for dep in info["depends_on"]:
            if dep not in pkgs:
                continue
            dep_rank = TYPE_RANK.get(pkgs[dep]["type"], 99)
            # 依赖方不能比被依赖方更底层
            if self_rank < dep_rank:
                errs.append(
                    f"  ✗ {name}({info['type']}) 不允许依赖 {dep}"
                    f"({pkgs[dep]['type']}): 违反分层约束"
                )
    return errs


def check_existence(pkgs: dict) -> list:
    errs = []
    for name, info in pkgs.items():
        for dep in info["depends_on"]:
            if dep not in pkgs:
                errs.append(f"  ✗ {name}: depends_on 引用了不存在的包 '{dep}'")
    return errs


def check_placeholders(pkgs: dict) -> list:
    """检测 depends_on/subpackages 里未替换的脚手架占位符。"""
    errs = []
    for name, info in pkgs.items():
        for dep in info["depends_on"]:
            if "TODO" in dep or "replace_me" in dep:
                errs.append(f"  ✗ {name}: 依赖 '{dep}' 含未替换的占位符")
    return errs


def topo_sort(pkgs: dict) -> list | None:
    """返回拓扑序；存在环则返回 None。"""
    in_deg = {n: 0 for n in pkgs}
    adj = {n: [] for n in pkgs}
    for name, info in pkgs.items():
        for dep in info["depends_on"]:
            if dep in pkgs:
                adj[dep].append(name)
                in_deg[name] += 1
    queue = sorted(n for n, d in in_deg.items() if d == 0)
    order = []
    while queue:
        n = queue.pop(0)
        order.append(n)
        for m in sorted(adj[n]):
            in_deg[m] -= 1
            if in_deg[m] == 0:
                queue.append(m)
        queue.sort()
    return order if len(order) == len(pkgs) else None


def main() -> int:
    if not SRC.exists():
        print(f"错误: {SRC} 不存在", file=sys.stderr)
        return 1

    print("== 依赖链校验 ==")
    pkgs = load_packages()
    if not pkgs:
        print("  (无包)")
        return 0

    errors = []
    errors += check_existence(pkgs)
    errors += check_placeholders(pkgs)
    errors += check_layering(pkgs)

    cycles = detect_cycles(pkgs)
    for c in cycles:
        errors.append(f"  ✗ 循环依赖: {' → '.join(c)}")

    if errors:
        for e in errors:
            print(e)
        return 1

    order = topo_sort(pkgs)
    print("  ✓ 无循环依赖、引用完整、分层合法")
    print("  编译顺序（拓扑序）:")
    for i, n in enumerate(order, 1):
        print(f"    {i}. {n} ({pkgs[n]['type']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
