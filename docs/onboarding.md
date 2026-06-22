# 新人上手指南

> 目标：从 clone 到 `colcon test` 全绿，再创建你的第一个包，预计 30~60 分钟。

## 0. 你需要先知道的

这是一个 **ROS2 工作空间模板**，把每个功能包强制拆成三层：

| 层 | 职责 | 能否依赖 ROS2 |
|----|------|--------------|
| `model` | 纯数据结构（DTO） | ❌ 不能 |
| `service` | 纯业务逻辑（可单测） | ❌ 不能 |
| `controller` | ROS2 适配（收发消息、转日志） | ✅ 唯一可以 |

这样做的好处：**核心算法可以脱离 ROS2 用 gtest 直接测**，换届不丢。

每个包还必须有一份 `plugin.yaml`，声明它的 ROS2 接口契约（topic 输入输出、参数、依赖），CI 会自动校验。

## 1. 环境准备

```bash
# Ubuntu 22.04 + ROS2 Humble（开发基准）
sudo apt install ros-humble-desktop python3-colcon-common-extensions
sudo apt install python3-pip nodejs npm graphviz   # 校验工具链
pip3 install pyyaml jsonschema pre-commit
npm install -g ajv-cli ajv-formats
source /opt/ros/humble/setup.bash
```

## 2. 拉取并构建

```bash
git clone <本仓库> my_robot_ws && cd my_robot_ws
rosdep install --from-paths src --ignore-src -r -y   # 装系统依赖
colcon build --symlink-install                        # 构建
source install/setup.bash
colcon test --return-code-on-test-failure            # 跑全部测试
colcon test-result --verbose                         # 看结果
```

构建顺序由 `make validate-deps` 输出的拓扑序决定，colcon 会自动按依赖排序。

## 3. 提交前自检（最重要）

```bash
make validate-all    # schema + 交叉 + 依赖链 + topic 命名，<5 秒
```

这条命令 **必须全绿才能提交**。CI 跑的是同一套校验，本地过了 CI 一般就过了。

如果装了 pre-commit（`pre-commit install`），提交时会自动跑格式化和 schema 校验。

## 4. 创建你的第一个包

按类型选模板，一行命令：

```bash
make new-node    NAME=my_detector      # 业务节点（有 ROS2 节点）
make new-lib     NAME=my_utils         # 纯 C++ 库
make new-msgs    NAME=my_msgs          # 自定义消息
make new-bringup NAME=my_bringup       # 集成 launch 包
```

生成的包骨架已经填好三层结构、占位符（`__PACKAGE_NAME__`）已替换、命名空间和 include 路径都对齐。你只需：

1. 改 `package.xml` 的 `maintainer` / `license`
2. 改 `plugin.yaml` 填真实接口（topic / 参数 / 依赖）
3. 写 `model` → `service` → `controller`
4. 在 `test/` 里给 service 层写 gtest
5. `make validate-all` → 提交

> ⚠ 包名即约定：**包名 == C++ 命名空间 == include 目录**。三者必须一致，脚手架已保证。

## 5. 看懂现有代码

从 `robot_control`（最典型的 MSC 节点）开始读：

```
src/robot_control/
├── include/robot_control/
│   ├── model/types.hpp              # Threat、TwistCmd、Config
│   ├── service/safety_velocity.hpp  # 用 robot_common::PID 算避障速度
│   └── controller/main_node.hpp     # 订阅 obstacles → 发布 cmd_vel
├── test/test_safety_velocity.cpp    # 纯逻辑测试，不碰 ROS2
└── plugin.yaml                      # 接口契约
```

`controller` 里你能看到三件事：参数声明、`model↔ROS` 类型转换、异常转日志。**它不该有业务逻辑**——逻辑全在 `service`。

## 6. 跑起来看效果

```bash
# 终端1：完整系统（hardware + perception + control）
ros2 launch robot_bringup full_system.launch.py

# 终端2：仿真（复用 full_system，强制 use_sim_time）
ros2 launch robot_bringup sim.launch.py

# 看话题
ros2 topic list
ros2 topic echo /robot_control/output/cmd_vel
```

## 7. 遇到问题

- 校验失败 → 看错误里的 `@路径`，定位到 `plugin.yaml` 的具体字段
- 编译顺序错乱 → `make validate-deps`，检查 `depends_on` 是否声明全
- 想知道"为什么这么设计" → 读 `docs/lessons_learned.md`（最重要）
- 命名拿不准 → 读 `docs/conventions.md`
