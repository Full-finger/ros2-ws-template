#!/usr/bin/env python3
"""
scripts/arch_check.py

架构合规性与代码质量报告生成器。

借鉴分层检查理念，适配 ROS2/C++ 三层架构（model/service/controller）。
与 validate_*.py 互补：
  - validate_*.py  → 接口契约合规（plugin.yaml/package.xml/include 边界/依赖链/命名）
  - arch_check.py  → 架构完整性与代码质量（三层完整性、测试覆盖度、文件规模、TODO）

输出 docs/arch-report.md（AI/人易读的结构化 Markdown）+ 控制台彩色摘要。
零外部依赖（仅 stdlib）。退出码：0 全绿，1 有发现。
"""
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
REPORT = ROOT / "docs" / "arch-report.md"

# ── 颜色（非 TTY 自动禁用） ──
IS_TTY = sys.stdout.isatty()
if IS_TTY:
    GREEN, RED, YELLOW, CYAN, RESET = (
        "\033[32m", "\033[31m", "\033[33m", "\033[36m", "\033[0m")
else:
    GREEN = RED = YELLOW = CYAN = RESET = ""

# ── 各层文件行数阈值（参考 reconnaissance 实测，留足余量） ──
LINE_THRESHOLDS = {
    "model": 200,      # 数据结构，应很短
    "service": 300,    # 业务逻辑，conventions 说 >200 行才拆 .cpp
    "controller": 400, # ROS2 适配，允许稍长
    "library": 300,    # 纯 C++ 库
    "test": 400,       # 测试可稍长
}
INCLUDE_THRESHOLD = 20  # 单文件 #include 数量上限


@dataclass
class Finding:
    level: str        # ✅/⚠️/❌ 对应 ok/warn/error
    rule: str
    file: str
    line: int
    message: str


@dataclass
class ReportData:
    a1_layer_completeness: list[Finding] = field(default_factory=list)
    a2_test_coverage: list[tuple] = field(default_factory=list)  # (pkg, service, lang, has_test)
    b1_large_files: list[Finding] = field(default_factory=list)
    b2_todos: list[Finding] = field(default_factory=list)
    b3_many_includes: list[Finding] = field(default_factory=list)
    scanned_files: int = 0


def _read_plugin_meta(pf: Path) -> dict:
    """轻量读取 plugin.yaml 的顶层 type/language，不引 pyyaml（保持零依赖）。

    只认行首无缩进的 `type:` / `language:`（避免被 parameters 里的
    `- type: double` 这种子字段误导）。
    """
    meta = {"type": None, "language": "cpp"}
    for line in pf.read_text(encoding="utf-8").splitlines():
        # 顶层键：行首就是 `type:` 或 `language:`（无缩进）
        if line.startswith("type:"):
            meta["type"] = line.split("#", 1)[0].split(":", 1)[1].strip()
        elif line.startswith("language:"):
            meta["language"] = line.split("#", 1)[0].split(":", 1)[1].strip()
    return meta


def load_node_packages() -> list[tuple[str, Path, str]]:
    """返回所有 type=node 的 (包名, 包目录, 语言)。"""
    pkgs = []
    for d in sorted(p for p in SRC.iterdir() if p.is_dir()):
        pf = d / "plugin.yaml"
        if not pf.exists():
            continue
        meta = _read_plugin_meta(pf)
        if meta["type"] == "node":
            pkgs.append((d.name, d, meta["language"]))
    return pkgs


def check_layer_completeness(pkgs: list[tuple[str, Path, str]]) -> list[Finding]:
    """A1: node 包必须有三层 model/service/controller 目录且非空。

    C++:  include/<pkg>/model  等，文件 *.hpp
    Python: <pkg>/<pkg>/model 等，文件 *.py
    """
    findings = []
    for name, d, lang in pkgs:
        if lang == "python":
            root = d / name  # <pkg_dir>/<pkg>/
            suffix = "*.py"
        else:
            root = d / "include" / name
            suffix = "*.hpp"
        for layer in ("model", "service", "controller"):
            layer_dir = root / layer
            files = list(layer_dir.glob(suffix)) if layer_dir.exists() else []
            if not files:
                findings.append(Finding(
                    "❌", "A1-layer-complete",
                    f"src/{name}/{root.relative_to(d)}/{layer}/", 0,
                    f"node 包缺少 {layer} 层（目录不存在或无 {suffix.strip('*')})"))
    return findings


def check_test_coverage(pkgs: list[tuple[str, Path, str]]) -> list[tuple]:
    """A2: 每个 service 应有对应测试。返回 (pkg, service, lang, has_test)。

    C++:  service 在 include/<pkg>/service/*.hpp，对应 test/test_<svc>.cpp
    Python: service 在 <pkg>/<pkg>/service/*.py，对应 test/test_<svc>.py
    """
    rows = []
    for name, d, lang in pkgs:
        if lang == "python":
            svc_dir = d / name / "service"
            svc_suffix = ".py"
            test_suffix = ".py"
        else:
            svc_dir = d / "include" / name / "service"
            svc_suffix = ".hpp"
            test_suffix = ".cpp"
        test_dir = d / "test"
        if not svc_dir.exists():
            continue
        for svc in sorted(svc_dir.glob(f"*{svc_suffix}")):
            if svc.stem == "__init__":  # 跳过 Python 包初始化文件
                continue
            svc_stem = svc.stem  # differential_drive / obstacle_extractor
            expected = test_dir / f"test_{svc_stem}{test_suffix}"
            rows.append((name, svc_stem, lang, expected.exists()))
    return rows


def classify_layer(rel: Path) -> str:
    """根据文件相对路径判定所属层级（用于套用行数阈值）。"""
    parts = rel.parts
    if "test" in parts:
        return "test"
    if "model" in parts:
        return "model"
    if "service" in parts:
        return "service"
    if "controller" in parts:
        return "controller"
    return "library"


def scan_code_quality(data: ReportData) -> None:
    """B1/B2/B3: 扫描所有 .hpp/.cpp 的行数、TODO、include 数。"""
    todo_re = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
    for f in sorted(SRC.rglob("*")):
        if f.suffix not in (".hpp", ".cpp", ".h", ".cc", ".py"):
            continue
        if not f.is_file():
            continue
        data.scanned_files += 1
        rel = f.relative_to(ROOT)
        text = f.read_text(encoding="utf-8")
        lines = text.splitlines()
        line_count = len(lines)

        # B1 文件行数
        layer = classify_layer(rel)
        threshold = LINE_THRESHOLDS.get(layer, 300)
        if line_count > threshold:
            data.b1_large_files.append(Finding(
                "⚠️", f"B1-line-count({layer})",
                str(rel), line_count,
                f"{line_count} 行超过 {layer} 层阈值 {threshold}"))

        # B2 TODO/FIXME
        for i, line in enumerate(lines, 1):
            if todo_re.search(line):
                tag = todo_re.search(line).group(1)
                snippet = line.strip()[:80]
                data.b2_todos.append(Finding(
                    "ℹ️", f"B2-{tag}", str(rel), i, snippet))

        # B3 include 数（C++）。Python 包不适用，跳过
        if f.suffix == ".py":
            inc_count = 0
        else:
            inc_count = sum(1 for l in lines if l.strip().startswith("#include"))
        if inc_count > INCLUDE_THRESHOLD:
            data.b3_many_includes.append(Finding(
                "⚠️", "B3-many-includes",
                str(rel), inc_count,
                f"{inc_count} 个 #include 超过阈值 {INCLUDE_THRESHOLD}"))


def collect() -> ReportData:
    data = ReportData()
    pkgs = load_node_packages()
    data.a1_layer_completeness = check_layer_completeness(pkgs)
    data.a2_test_coverage = check_test_coverage(pkgs)
    scan_code_quality(data)
    return data


# ═══════════════════════════════════════════════════════════
#  报告生成（docs/arch-report.md）
# ═══════════════════════════════════════════════════════════
def md_severity_emoji(level: str) -> str:
    return {"❌": "❌", "⚠️": "⚠️", "ℹ️": "ℹ️"}.get(level, "❓")


def generate_report(data: ReportData) -> None:
    a1_count = len(data.a1_layer_completeness)
    a2_missing = sum(1 for *_, has in data.a2_test_coverage if not has)
    b1_count = len(data.b1_large_files)
    b2_count = len(data.b2_todos)
    b3_count = len(data.b3_many_includes)
    total_findings = a1_count + a2_missing + b1_count + b3_count  # B2 TODO 不计入"问题"

    lines = []
    lines.append("# 架构合规性与代码质量报告")
    lines.append("")
    lines.append("> 由 `scripts/arch_check.py` 自动生成。与 `validate_*.py`（接口契约）互补，"
                 "专注**架构完整性**与**代码质量**。")
    lines.append(">")
    lines.append("> **核心原则**：每个 node 包强制 model/service/controller 三层；"
                 "service 零 ROS2 依赖且必有 gtest；删掉 controller，service 能独立编译。")
    lines.append(">")
    lines.append("> ⚠️ **免责声明**：本工具仅做结构性检查与模式匹配，"
                 "存在漏报和误报，不能替代 code review。")
    lines.append("")
    lines.append(f"生成时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"扫描文件：{data.scanned_files} 个源文件")
    lines.append("")

    # ── 1. 汇总 ──
    lines.append("## 1. 汇总")
    lines.append("")
    lines.append("| 类别 | 检查项 | 发现数 |")
    lines.append("|---|---|---|")
    lines.append(f"| A1 — 三层完整性 | node 包 model/service/controller 目录 | "
                 f"{GREEN if a1_count == 0 else RED}{a1_count}{RESET} |")
    lines.append(f"| A2 — 测试覆盖度 | service 缺少对应 gtest | "
                 f"{GREEN if a2_missing == 0 else RED}{a2_missing}{RESET} |")
    lines.append(f"| B1 — 文件行数 | 超出层级阈值 | "
                 f"{GREEN if b1_count == 0 else YELLOW}{b1_count}{RESET} |")
    lines.append(f"| B2 — 待办标记 | TODO/FIXME/HACK | "
                 f"{CYAN}{b2_count}{RESET} |")
    lines.append(f"| B3 — include 数 | 单文件 #include 过多 | "
                 f"{GREEN if b3_count == 0 else YELLOW}{b3_count}{RESET} |")
    lines.append("")
    lines.append(f"**问题总计：{total_findings}**"
                 f"（B2 待办标记仅供参考，不计入问题数）")
    lines.append("")

    # ── 2. 架构层级图 ──
    lines.append("## 2. 架构层级图")
    lines.append("")
    lines.append("```mermaid")
    lines.append("graph TD")
    lines.append("    subgraph 包内三层")
    lines.append('        M["📊 model<br/><small>纯数据结构 · 零 ROS2</small>"]')
    lines.append('        S["⚙️ service<br/><small>纯业务逻辑 · 必有 gtest</small>"]')
    lines.append('        C["📋 controller<br/><small>ROS2 适配 · 唯一接触 rclcpp</small>"]')
    lines.append("    end")
    lines.append('    ROS["🔄 rclcpp / *_msgs<br/><small>仅 controller 可 include</small>"]')
    lines.append("    C --> S --> M")
    lines.append("    C -.->|转换/收发| ROS")
    lines.append('    S -.- T["✅ gtest<br/><small>裸跑 service</small>"]')
    lines.append("```")
    lines.append("")

    # ── 3. A 类详情 ──
    lines.append("## 3. 架构完整性（A 类）")
    lines.append("")
    lines.append("### 3a. A1 — 三层目录完整性")
    lines.append("")
    if not data.a1_layer_completeness:
        lines.append("✅ 所有 node 包的 model/service/controller 三层目录齐全。")
    else:
        lines.append("| 级别 | 规则 | 路径 | 说明 |")
        lines.append("|---|---|---|---|")
        for f in data.a1_layer_completeness:
            lines.append(f"| {md_severity_emoji(f.level)} | `{f.rule}` | `{f.file}` | {f.message} |")
    lines.append("")

    lines.append("### 3b. A2 — Service 测试覆盖度")
    lines.append("")
    if not data.a2_test_coverage:
        lines.append("（无 node 包）")
    else:
        lines.append("| 包 | service | 有测试 |")
        lines.append("|---|---|---|")
        for pkg, svc, lang, has in data.a2_test_coverage:
            mark = "✅" if has else "❌"
            lines.append(f"| `{pkg}` | `{svc}` ({lang}) | {mark} |")
    lines.append("")

    # ── 4. B 类详情 ──
    lines.append("## 4. 代码质量（B 类）")
    lines.append("")

    lines.append("### 4a. B1 — 文件行数过多")
    lines.append("")
    if not data.b1_large_files:
        lines.append("✅ 所有源文件在层级阈值内。")
    else:
        lines.append("| 级别 | 文件 | 行数 | 说明 |")
        lines.append("|---|---|---|---|")
        for f in data.b1_large_files:
            lines.append(f"| {md_severity_emoji(f.level)} | `{f.file}` | {f.line} | {f.message} |")
    lines.append("")

    lines.append("### 4b. B2 — 待办标记（TODO/FIXME）")
    lines.append("")
    if not data.b2_todos:
        lines.append("✅ 无待办标记。")
    else:
        lines.append("| 标记 | 文件 | 行号 | 内容 |")
        lines.append("|---|---|---|---|")
        for f in data.b2_todos:
            lines.append(f"| {md_severity_emoji(f.level)} | `{f.file}` | {f.line} | {f.message} |")
    lines.append("")

    lines.append("### 4c. B3 — 单文件 include 过多")
    lines.append("")
    if not data.b3_many_includes:
        lines.append("✅ 所有文件 #include 数在阈值内。")
    else:
        lines.append("| 级别 | 文件 | include 数 | 说明 |")
        lines.append("|---|---|---|---|")
        for f in data.b3_many_includes:
            lines.append(f"| {md_severity_emoji(f.level)} | `{f.file}` | {f.line} | {f.message} |")
    lines.append("")

    # ── 5. 附录 ──
    lines.append("## 5. 附录：检查规则说明")
    lines.append("")
    lines.append("### 与 validate_*.py 的分工")
    lines.append("")
    lines.append("| 工具 | 关注点 | 示例 |")
    lines.append("|---|---|---|")
    lines.append("| `validate_*.py`（5 个） | **接口契约** | plugin.yaml ↔ package.xml 一致性、include 边界、依赖链分层、topic 命名 |")
    lines.append("| `arch_check.py`（本工具） | **架构完整性与代码质量** | 三层目录齐全、service 有测试、文件规模、TODO |")
    lines.append("")
    lines.append("### 各层职责（参见 docs/conventions.md）")
    lines.append("")
    lines.append("| 层 | 允许 | 禁止 |")
    lines.append("|---|---|---|")
    lines.append("| **model** | 纯数据结构 | 任何逻辑、ROS2 |")
    lines.append("| **service** | 纯业务逻辑、调 model | `rclcpp/*`、`*_msgs/*` |")
    lines.append("| **controller** | ROS2 收发、类型转换 | 业务逻辑（只能调 service） |")
    lines.append("")
    lines.append("### 文件行数阈值")
    lines.append("")
    lines.append("| 层 | 阈值 | 依据 |")
    lines.append("|---|---|---|")
    lines.append(f"| model | {LINE_THRESHOLDS['model']} | 数据结构应简短 |")
    lines.append(f"| service | {LINE_THRESHOLDS['service']} | conventions 约定 >200 行拆 .cpp |")
    lines.append(f"| controller | {LINE_THRESHOLDS['controller']} | 允许稍长（含 ROS2 胶水） |")
    lines.append(f"| library | {LINE_THRESHOLDS['library']} | 纯 C++ 库 |")
    lines.append(f"| test | {LINE_THRESHOLDS['test']} | 测试可稍长 |")
    lines.append("")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")


# ═══════════════════════════════════════════════════════════
#  控制台摘要
#═══════════════════════════════════════════════════════════
def console_summary(data: ReportData) -> int:
    a1 = len(data.a1_layer_completeness)
    a2 = sum(1 for *_, has in data.a2_test_coverage if not has)
    b1 = len(data.b1_large_files)
    b2 = len(data.b2_todos)
    b3 = len(data.b3_many_includes)
    problems = a1 + a2 + b1 + b3

    def fmt(n, warn=False):
        if n == 0:
            return f"{GREEN}✅ 0{RESET}"
        color = YELLOW if warn else RED
        return f"{color}{'⚠️' if warn else '❌'} {n}{RESET}"

    print(f"\n{CYAN}═══════════════════════════════════════════════════{RESET}")
    print(f"{CYAN}  架构合规性与代码质量检查{RESET}")
    print(f"{CYAN}═══════════════════════════════════════════════════{RESET}\n")
    print(f"  {CYAN}── A 架构完整性 ──{RESET}")
    print(f"  {'A1 — 三层目录完整性':<30} {fmt(a1)}")
    print(f"  {'A2 — service 测试覆盖度':<30} {fmt(a2)}")
    print(f"\n  {CYAN}── B 代码质量 ──{RESET}")
    print(f"  {'B1 — 文件行数过多':<30} {fmt(b1, warn=True)}")
    print(f"  {'B2 — TODO/FIXME 标记':<30} {CYAN}ℹ️ {b2}{RESET}")
    print(f"  {'B3 — include 数过多':<30} {fmt(b3, warn=True)}")
    print()
    if problems == 0:
        print(f"{GREEN}  ✅ 架构检查通过（{data.scanned_files} 文件扫描，"
              f"{b2} 个待办标记仅供参考）{RESET}")
    else:
        print(f"{YELLOW}  ⚠ 发现 {problems} 个问题"
              f"（详见 {REPORT.relative_to(ROOT)}）{RESET}")
    print()
    return 1 if problems else 0


def main() -> int:
    if not SRC.exists():
        print(f"错误: {SRC} 不存在", file=sys.stderr)
        return 1
    data = collect()
    generate_report(data)
    return console_summary(data)


if __name__ == "__main__":
    sys.exit(main())
