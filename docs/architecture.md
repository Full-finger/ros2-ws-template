# 系统架构

## 包依赖图

```
robot_msgs ─────┬──→ robot_hardware ──┐
                ├──→ robot_perception_py ─┼──→ robot_bringup
                └──→ robot_control ──────┘   （集成层，编排启动）

robot_common ────→ robot_hardware            （运动学用其 math 工具）
```

`robot_msgs` 与 `robot_common` 平级、互不依赖。`robot_msgs` 是所有业务包的公共消息底座；`robot_common` 提供 C++ 工具，示范工程中 `robot_hardware` 用了它的数学工具。

**混合语言**：hardware/control 是 C++（实时层），perception 是 Python（AI/快速迭代层）。

> 图的 dot 源：`docs/dependency_graph.dot`（由 `make graph` 重新生成）。

## 包职责

| 包 | 类型 | 职责 |
|----|------|------|
| `robot_msgs` | messages | 团队公共 msg/srv/action（`MotorState`、`ObstacleArray`、`EmergencyStop`…） |
| `robot_common` | library | 纯 C++ 工具（PID 控制器、数学工具），**零 ROS2 依赖** |
| `robot_hardware` | node | 差速驱动运动学、里程计发布、紧急停止服务 |
| `robot_perception_py` | node (Python) | 激光点求质心，输出障碍物列表 |
| `robot_control` | node | 基于距离阈值的避障速度调节，输出 `cmd_vel` |
| `robot_bringup` | bringup | launch 文件 + 系统级配置，编排上述节点的启动 |

## 分层约束（编译期可校验）

依赖方向只能从底层往上，`make validate-deps` 会强制：

```
messages(0) < library(1) < node(2) < bringup(3)
```

- `messages` 不能依赖任何包
- `library` 不能依赖 `node` / `bringup`
- `node` 不能依赖 `bringup`
- 禁止循环依赖

## 运行时数据流

```
                       sensor_msgs/LaserScan（外部）
                              │
                              ▼
  ┌─────────────────┐   ┌──────────────────┐
  │ robot_hardware  │   │ robot_perception_py│
  │  轮速读数       │   │  质心提取         │
  │  → 运动学积分   │   │  → 障碍物列表    │
  └────────┬────────┘   └────────┬─────────┘
           │                     │
   nav_msgs/Odometry    robot_msgs/ObstacleArray
           │                     │
           └─────────┬───────────┘
                     ▼
            ┌─────────────────┐
            │  robot_control  │
            │  阈值避障       │
            │  → cmd_vel      │
            └─────────────────┘
                     │
              geometry_msgs/Twist
```

`robot_hardware` 同时提供 `~/emergency_stop` 服务，任一节点都能紧急停车并重置里程计。

## 三层架构（model / service / controller）

每个 `node` 类型包内部强制三层：

```
include/<pkg>/
├── model/         纯数据结构（零 ROS2、零逻辑）
│   ├── types.hpp
│   └── errors.hpp
├── service/       纯业务逻辑（零 ROS2，可 gtest）
│   └── xxx.hpp    小型 header-only；大型拆 .cpp
└── controller/
    └── main_node.hpp   唯一接触 rclcpp 的地方
src/<pkg>/
└── controller/
    └── main_node.cpp   编译入口
```

**职责边界：**

- `controller` 只做四件事：声明参数、订阅/发布、`model ↔ ROS` 类型转换、异常转日志。
- 业务逻辑全在 `service`，输入输出都是 `model` 类型。
- `service` 不 `#include` 任何 `rclcpp/*` 或 `*_msgs/*`。

**为什么这样分？** 见 `docs/lessons_learned.md` 的"为什么要拆三层"。一句话：算法能在 CI 上裸跑 gtest，换 ROS2 发行版也不影响核心逻辑。

## 配置层级

参数有三层，后者覆盖前者：

1. `plugin.yaml` 的 `parameters[].default` —— 声明 + 文档（默认值）
2. `<pkg>/config/params.yaml` —— 包级调优
3. `robot_bringup/config/system.yaml` —— 系统级覆盖

三者都受 `schemas/params.schema.json` 校验。
