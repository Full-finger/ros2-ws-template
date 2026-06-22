#!/usr/bin/env bash
# scripts/new_pkg.sh — 创建新包（替代 Makefile 里的 _create_pkg 宏）
#
# 用法:
#   scripts/new_pkg.sh <type> <name>
#   make new-node    NAME=robot_foo   → 调用本脚本 type=node
#   make new-lib     NAME=robot_foo   → type=library
#   make new-msgs    NAME=robot_foo   → type=messages
#   make new-bringup NAME=robot_foo   → type=bringup
#
# 处理:
#   1. 校验包名格式
#   2. cp 模板到 src/<name>
#   3. sed 替换文件内容里的 __PACKAGE_NAME__
#   4. 重命名目录 include/__PACKAGE_NAME__ → include/<name>
#   5. 重命名文件 __PACKAGE_NAME__.* → <name>.*

set -euo pipefail

# ── 颜色 ──
if [ -t 1 ]; then
    GREEN=$'\033[32m'; RED=$'\033[31m'; YELLOW=$'\033[33m'; RESET=$'\033[0m'
else
    GREEN=""; RED=""; YELLOW=""; RESET=""
fi

TYPE="${1:-}"
NAME="${2:-}"

# ── type → 模板目录 映射 ──
case "$TYPE" in
    node)     TMPL="new_node" ;;
    node-py)  TMPL="new_node_py" ;;
    library)  TMPL="new_library" ;;
    msgs)     TMPL="new_msgs" ;;
    bringup)  TMPL="new_bringup" ;;
    "")
        echo "${RED}错误: 缺少 type 参数${RESET}"
        echo "用法: $0 <node|node-py|library|msgs|bringup> <name>"
        exit 1
        ;;
    *)
        echo "${RED}错误: 未知 type '$TYPE'${RESET}"
        echo "合法值: node | node-py | library | msgs | bringup"
        exit 1
        ;;
esac

# ── 校验包名 ──
if [ -z "$NAME" ]; then
    echo "${RED}错误: 缺少 name 参数${RESET}"
    echo "用法: $0 <node|node-py|library|msgs|bringup> <name>"
    exit 1
fi
if ! echo "$NAME" | grep -qE '^[a-z][a-z0-9_]*$'; then
    echo "${RED}错误: 包名 '$NAME' 不合法${RESET}"
    echo "规则: 小写字母开头，只含 [a-z0-9_]"
    exit 1
fi

# ── 路径检查 ──
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMPL_DIR="$ROOT/templates/$TMPL"
DEST="$ROOT/src/$NAME"

if [ ! -d "$TMPL_DIR" ]; then
    echo "${RED}错误: 模板目录不存在 $TMPL_DIR${RESET}"
    exit 1
fi
if [ -d "$DEST" ]; then
    echo "${RED}错误: $DEST 已存在${RESET}"
    exit 1
fi

# ── 复制 ──
echo "${GREEN}==> 创建 [$TYPE] 包: $NAME${RESET}"
mkdir -p "$ROOT/src"
cp -r "$TMPL_DIR" "$DEST"

# ── 1) 替换文件内容里的占位符 ──
echo "${YELLOW}    替换占位符 __PACKAGE_NAME__ → $NAME${RESET}"
find "$DEST" -type f \
    \( -name "*.hpp" -o -name "*.cpp" -o -name "*.yaml" \
       -o -name "*.xml" -o -name "*.py" -o -name "CMakeLists.txt" \
       -o -name "*.msg" -o -name "*.srv" -o -name "*.action" \
       -o -name "setup.cfg" \) \
    -exec sed -i "s/__PACKAGE_NAME__/$NAME/g" {} +

# ── 2) 重命名目录占位符 ──
# C++: include/__PACKAGE_NAME__ → include/<NAME>
if [ -d "$DEST/include/__PACKAGE_NAME__" ]; then
    echo "${YELLOW}    重命名 include/__PACKAGE_NAME__ → include/$NAME${RESET}"
    mv "$DEST/include/__PACKAGE_NAME__" "$DEST/include/$NAME"
fi
# Python: <pkg>/__PACKAGE_NAME__/ → <pkg>/<NAME>/ （Python 模块目录）
if [ -d "$DEST/__PACKAGE_NAME__" ]; then
    echo "${YELLOW}    重命名 __PACKAGE_NAME__/ → $NAME/${RESET}"
    mv "$DEST/__PACKAGE_NAME__" "$DEST/$NAME"
fi
# Python: resource/__PACKAGE_NAME__ → resource/<NAME>（ament_python 必需的 marker）
if [ -f "$DEST/resource/__PACKAGE_NAME__" ]; then
    echo "${YELLOW}    重命名 resource/__PACKAGE_NAME__ → resource/$NAME${RESET}"
    mv "$DEST/resource/__PACKAGE_NAME__" "$DEST/resource/$NAME"
fi

# ── 3) 重命名 __PACKAGE_NAME__.* 文件 → <NAME>.* ──
find "$DEST" -type f -name "__PACKAGE_NAME__.*" | while read -r f; do
    dir="$(dirname "$f")"
    ext="${f##*__PACKAGE_NAME__}"
    newf="$dir/$NAME$ext"
    echo "${YELLOW}    重命名 $(basename "$f") → $(basename "$newf")${RESET}"
    mv "$f" "$newf"
done

echo "${GREEN}✓ 已创建 $DEST${RESET}"
echo ""
echo "下一步:"
echo "  cd $DEST"
echo "  # 编辑 plugin.yaml 填写真实接口契约"
echo "  # 编辑 package.xml 填写 maintainer/license"
echo "  # 提交前运行: make validate-all"
