#!/usr/bin/env python3
"""
scripts/validate_schema.py

用 JSON Schema 校验本项目所有声明文件:
  - src/*/plugin.yaml         → schemas/plugin.schema.json
  - src/*/config/*.yaml       → schemas/params.schema.json
  - schemas/*.json            → 自身合法性检查

退出码: 0 全部通过, 1 有错误。
"""
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "schemas"
SRC = ROOT / "src"

# 复用 Validator 实例（已编译 schema）
_validator_cache: dict = {}


def get_validator(name: str) -> Draft7Validator:
    if name not in _validator_cache:
        path = SCHEMAS / name
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft7Validator.check_schema(schema)
        _validator_cache[name] = Draft7Validator(schema)
    return _validator_cache[name]


def fmt_errors(errors) -> list:
    out = []
    for e in errors:
        loc = "/" + "/".join(str(p) for p in e.absolute_path) if e.absolute_path else "(root)"
        out.append(f"    @{loc}: {e.message}")
    return out


def validate_plugin_yamls() -> int:
    print("== 校验 plugin.yaml (plugin.schema.json) ==")
    validator = get_validator("plugin.schema.json")
    files = sorted(SRC.glob("*/plugin.yaml"))
    if not files:
        print("  (无 plugin.yaml)")
    total = 0
    for f in files:
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        errs = list(validator.iter_errors(data))
        rel = f.relative_to(ROOT)
        if errs:
            total += len(errs)
            print(f"  ✗ {rel}: {len(errs)} 个错误")
            for line in fmt_errors(errs):
                print(line)
        else:
            print(f"  ✓ {rel}")
    return total


def validate_config_yamls() -> int:
    print("== 校验 config/*.yaml (params.schema.json) ==")
    validator = get_validator("params.schema.json")
    files = sorted(SRC.glob("*/config/*.yaml"))
    if not files:
        print("  (无 config yaml)")
    total = 0
    for f in files:
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        rel = f.relative_to(ROOT)
        if data is None:  # 空配置文件（全注释），合法跳过
            print(f"  ○ {rel} (空)")
            continue
        errs = list(validator.iter_errors(data))
        if errs:
            total += len(errs)
            print(f"  ✗ {rel}: {len(errs)} 个错误")
            for line in fmt_errors(errs):
                print(line)
        else:
            print(f"  ✓ {rel}")
    return total


def main() -> int:
    if not SRC.exists():
        print(f"错误: {SRC} 不存在", file=sys.stderr)
        return 1

    total = 0
    total += validate_plugin_yamls()
    print()
    total += validate_config_yamls()
    print()

    if total:
        print(f"✗ 共 {total} 个 schema 校验错误")
        return 1
    print("✓ 所有 schema 校验通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
