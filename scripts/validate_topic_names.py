#!/usr/bin/env python3
"""
scripts/validate_topic_names.py

读取 schemas/topic_naming.schema.json（命名规范规则集），
遍历所有 plugin.yaml 的 inputs/outputs，逐条校验 topic 命名。

规则:
  - snake_case: 每个分段只含小写字母/数字/下划线
  - 私有 topic (~ 后第一段) 必须落在 semantic_groups 的某个 prefix
  - topic 深度: 私有 topic (~ 后段数) >= style.max_depth
  - 任何分段不得命中 forbidden.words
  - 整个 topic 不得命中 forbidden.patterns 任一正则

依赖: pyyaml。退出码: 0 通过, 1 有错误。
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
RULES_PATH = ROOT / "schemas" / "topic_naming.json"
SCHEMA_PATH = ROOT / "schemas" / "topic_naming.schema.json"


def load_rules() -> dict:
    import json
    from jsonschema import Draft7Validator
    if not RULES_PATH.exists():
        print(f"错误: 缺少 {RULES_PATH}", file=sys.stderr)
        sys.exit(1)
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    # 规则文档本身须符合其 schema
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft7Validator(schema).validate(rules)
    return rules


def segments(topic: str) -> list:
    """去掉 ~ 前缀，按 / 拆分段。"""
    t = topic.removeprefix("~")
    return [s for s in t.split("/") if s]


def is_snake(seg: str) -> bool:
    return re.match(r"^[a-z][a-z0-9_]*$", seg) is not None


def check_topic(topic: str, rules: dict, src: str) -> list:
    errs = []
    style = rules["style"]
    segs = segments(topic)
    allowed_prefixes = {g["prefix"] for g in rules["semantic_groups"]}

    # snake_case
    for s in segs:
        if not is_snake(s):
            errs.append(f"    {src}: 分段 '{s}' 不符合 snake_case")

    # 私有 topic 第一段必须是允许的语义前缀
    if topic.startswith("~/"):
        first = segs[0] if segs else ""
        if first and first not in allowed_prefixes:
            errs.append(f"    {src}: 私有 topic 首段 '{first}' 不在语义前缀列表 "
                        f"{sorted(allowed_prefixes)}")

        # 深度
        if len(segs) < style["max_depth"]:
            errs.append(f"    {src}: 私有 topic 层级过浅 (需要 >= {style['max_depth']})")

    # forbidden words
    for s in segs:
        if s in rules["forbidden"]["words"]:
            errs.append(f"    {src}: 分段 '{s}' 命中禁用词")

    # forbidden patterns
    for pat in rules["forbidden"]["patterns"]:
        if re.search(pat, topic):
            errs.append(f"    {src}: topic 命中禁用正则 /{pat}/")

    return errs


def main() -> int:
    if not RULES_PATH.exists():
        print(f"错误: 缺少 {RULES_PATH}", file=sys.stderr)
        return 1
    rules = load_rules()
    all_errors = []

    print("== topic 命名规范校验 ==")
    for pf in sorted(SRC.glob("*/plugin.yaml")):
        data = yaml.safe_load(pf.read_text(encoding="utf-8"))
        runtime = data.get("runtime", {}) or {}
        pkg = pf.parent.name
        for direction in ("inputs", "outputs"):
            for t in runtime.get(direction, []) or []:
                topic = t.get("topic", "")
                all_errors += check_topic(topic, rules, f"{pkg}.{direction} '{topic}'")
        print(f"  ✓ {pkg}")

    if all_errors:
        print(f"\n发现 {len(all_errors)} 个命名问题:")
        for e in all_errors:
            print(e)
        return 1
    print("✓ 所有 topic 命名合法")
    return 0


if __name__ == "__main__":
    sys.exit(main())
