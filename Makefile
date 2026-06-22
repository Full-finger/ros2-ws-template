.DEFAULT_GOAL := help

# ── 颜色（非 TTY 自动禁用） ──
ifneq (,$(filter $(MAKECMDGOALS),help))
IS_TTY :=
else
IS_TTY := $(shell [ -t 1 ] && echo 1)
endif
ifeq ($(IS_TTY),1)
GREEN  := \033[32m
RED    := \033[31m
YELLOW := \033[33m
RESET  := \033[0m
else
GREEN  := ""
RED    := ""
YELLOW := ""
RESET  := ""
endif

PYTHON := python3
SCRIPTS := scripts

# ═══════════════════════════════════════════════════════════
#  脚手架
# ═══════════════════════════════════════════════════════════
.PHONY: new-node new-lib new-msgs new-bringup
new-node: ## 创建业务节点包：make new-node NAME=robot_foo
	@$(SCRIPTS)/new_pkg.sh node $(NAME)

new-lib: ## 创建纯 C++ 库包：make new-lib NAME=robot_foo
	@$(SCRIPTS)/new_pkg.sh library $(NAME)

new-msgs: ## 创建消息定义包：make new-msgs NAME=robot_foo
	@$(SCRIPTS)/new_pkg.sh msgs $(NAME)

new-bringup: ## 创建集成包：make new-bringup NAME=robot_foo
	@$(SCRIPTS)/new_pkg.sh bringup $(NAME)

# ═══════════════════════════════════════════════════════════
#  校验
# ═══════════════════════════════════════════════════════════
.PHONY: validate-all validate-schema validate-cross validate-deps validate-topics validate-layers
validate-all: validate-schema validate-cross validate-deps validate-topics validate-layers ## 全部校验（提交前必跑）
	@printf "$(GREEN)✓ 所有校验通过$(RESET)\n"

validate-schema: ## JSON Schema 校验 plugin.yaml / config yaml
	@$(PYTHON) $(SCRIPTS)/validate_schema.py

validate-cross: ## plugin.yaml ↔ package.xml 一致性
	@$(PYTHON) $(SCRIPTS)/validate_cross.py

validate-deps: ## 依赖链完整性 + 分层合法性 + 拓扑序
	@$(PYTHON) $(SCRIPTS)/validate_deps.py

validate-topics: ## topic 命名规范
	@$(PYTHON) $(SCRIPTS)/validate_topic_names.py

validate-layers: ## 三层架构 include 边界（model/service/library 零 ROS2）
	@$(PYTHON) $(SCRIPTS)/validate_layers.py

# ═══════════════════════════════════════════════════════════
#  文档工具
# ═══════════════════════════════════════════════════════════
.PHONY: graph
graph: ## 重新生成依赖图 dot（需 graphviz 转 png）
	@$(PYTHON) $(SCRIPTS)/generate_dep_graph.py > docs/dependency_graph.dot
	@printf "$(GREEN)✓ 已生成 docs/dependency_graph.dot$(RESET)\n"
	@command -v dot >/dev/null 2>&1 && dot -Tpng docs/dependency_graph.dot -o docs/dependency_graph.png \
		&& printf "$(GREEN)✓ 已生成 docs/dependency_graph.png$(RESET)\n" \
		|| printf "$(YELLOW)提示：装 graphviz 后会自动生成 png$(RESET)\n"

# ═══════════════════════════════════════════════════════════
#  构建（依赖外部 ROS2 环境）
# ═══════════════════════════════════════════════════════════
.PHONY: build test clean
build: ## colcon 构建（需 source ROS2 环境）
	@colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release

test: ## colcon 测试
	@colcon test --return-code-on-test-failure
	@colcon test-result --verbose

clean: ## 清理构建产物
	@rm -rf build/ install/ log/

# ═══════════════════════════════════════════════════════════
#  帮助
# ═══════════════════════════════════════════════════════════
.PHONY: help
help: ## 显示此帮助
	@printf "\n$(GREEN)用法:$(RESET) make [target] [NAME=xxx]\n\n"
	@awk 'BEGIN {FS = ":.*##"; printf "  $(YELLOW)%-20s %s$(RESET)\n", "目标", "说明"} \
	      /^[a-zA-Z_-]+:.*?##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@printf "\n"
