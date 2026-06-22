# ros2-ws-template

一个**强约定、可校验**的 ROS2 工作空间模板。把每个功能包强制拆成 `model / service / controller` 三层，用 JSON Schema 卡住接口契约，让核心算法可脱离 ROS2 裸跑 gtest / pytest。

> 这是模板。`src/` 下的 6 个包（`robot_msgs` / `robot_common` / `robot_hardware` / `robot_perception_py` / `robot_control` / `robot_bringup`）是示范工程，替换成你自己的机器人代码即可。**C++ 与 Python 混合**：实时层（hardware/control）用 C++，AI/快速迭代层（perception）用 Python。

## 为什么用这个模板

- **三层架构**：业务逻辑（service）零 ROS2 依赖，换发行版只改 controller，算法在 CI 上秒级回归。
- **接口即契约**：每个包的 `plugin.yaml` 声明 topic/参数/依赖，CI 自动校验，文档与代码不漂移。
- **一键脚手架**：`make new-node NAME=xxx` 生成完整三层骨架，占位符、命名空间、include 路径全自动对齐。
- **<5 秒本地校验**：`make validate-all` 覆盖 schema、一致性、依赖链、命名规范，提交前必跑。

## 目录结构

```
.
├── Makefile                # 统一入口（建包 / 校验 / 构建）
├── schemas/                # 校验规则（plugin / params / topic_naming）
├── scripts/                # 脚手架与校验脚本
├── templates/              # 四类包模板（new_node / new_library / new_msgs / new_bringup）
├── docs/                   # 文档（onboarding / architecture / conventions / lessons_learned）
├── src/                    # 所有 ROS2 包（6 个示范包）
├── .github/workflows/ci.yml
├── .pre-commit-config.yaml
└── .clang-format
```

## 快速开始

**前置**：Ubuntu 22.04 + ROS2 Humble。

```bash
# 1. 装校验工具（schema 校验用）
pip install pyyaml jsonschema

# 2. 构建 + 测试（需 ROS2 环境）
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
colcon test --return-code-on-test-failure

# 3. 跑起来
ros2 launch robot_bringup full_system.launch.py
```

> 本地没有 ROS2 也能跑元校验：`make validate-all`。

## 创建新包

```bash
make new-node    NAME=robot_foo      # 业务节点（C++，实时层默认选这个）
make new-node-py NAME=robot_foo_py   # 业务节点（Python，AI/快速迭代用）
make new-lib     NAME=robot_foo      # 纯 C++ 库
make new-msgs    NAME=robot_foo      # 自定义消息
make new-bringup NAME=robot_foo      # 集成 launch 包
```

约定 **包名 == 命名空间 == 入口目录**，三者必须一致（脚手架已保证）。

### C++ 还是 Python？

| 场景 | 选 | 理由 |
|------|----|------|
| 控制循环、运动学、实时高频 | **C++** | 性能、类型安全、编译期保证 |
| AI/ML 推理、行为决策、快速原型 | **Python** | 生态、迭代速度、review 友好 |
| 纯工具库（PID、数学） | **C++** | 零 ROS2 依赖，可裸测 |

两层架构同样适用：Python 包的 model/service 仍禁止 `import rclpy`，pytest 裸测；`validate_layers` 对两种语言都校验。

## 校验

两套互补的检查：

- **接口契约**（`make validate-all`，提交前必跑）：schema、一致性、依赖链、命名、include 边界
- **架构与质量报告**（`make arch-check`）：三层完整性、service 测试覆盖度、文件规模、TODO 汇总，生成 `docs/arch-report.md`

```bash
make validate-all       # 全部（提交前必跑）
make validate-schema    # JSON Schema：plugin.yaml / config yaml
make validate-cross     # plugin.yaml ↔ package.xml 一致性
make validate-deps      # 依赖链完整性 + 分层合法性 + 拓扑序
make validate-topics    # topic 命名规范
make arch-check         # 架构与质量报告 → docs/arch-report.md
make graph              # 重新生成依赖图
```

## 三层架构

| 层 | 职责 | ROS2 依赖 |
|----|------|-----------|
| `model` | 纯数据结构 | ❌ |
| `service` | 纯业务逻辑（gtest 可测） | ❌ |
| `controller` | ROS2 适配（收发、转换、日志） | ✅ 唯一 |

判定标准：删掉 controller，service 能不能独立编译并过测试？能 → 合格。

## 文档

- [新人上手](docs/onboarding.md) — 从 0 到跑起来
- [系统架构](docs/architecture.md) — 包依赖、数据流、分层
- [开发规范](docs/conventions.md) — 命名、分层、契约
- [经验传承](docs/lessons_learned.md) — **最重要**，踩坑与决策的"为什么"
- [硬件清单](docs/hardware.md) — 部件与接线

## 示范包数据流

```
robot_hardware ──odom──┐
                       ├──→ robot_control ──cmd_vel──▶
robot_perception_py ──obstacles──┘
```

- `robot_hardware`（C++）：差速驱动运动学积分，发布 odom，提供紧急停止
- `robot_perception_py`（Python）：激光点求质心，输出障碍物列表
- `robot_control`（C++）：基于距离阈值的避障速度调节
- `robot_common`（C++）：纯 C++ 工具库（PID、数学工具），零 ROS2 依赖

## 约束速查

- 包类型 `plugin.yaml` 的 `type`：`library` / `node` / `messages` / `bringup`
- 依赖方向：`messages(0) < library(1) < node(2) < bringup(3)`，只能向上依赖
- topic：`snake_case`，私有用 `~/`，首段 ∈ {input, output, status, cmd, debug}

## 许可证

MIT
