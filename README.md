# ros2-ws-template

强约定、可机器校验的 ROS2 工作空间模板。

每个功能包强制 `model / service / controller` 三层，接口写成可校验契约，
核心算法脱离 ROS2 裸跑 gtest / pytest。`src/` 下 6 个包是示范工程，
替换成你自己的代码即可。实时层用 C++，AI / 快速迭代层用 Python。

## 特性

- **三层分离** — service 零 ROS2 依赖，删掉 controller 仍能编译并过测试
- **契约即代码** — 每包 `plugin.yaml` 声明 topic / 参数 / 依赖，6 个校验脚本 + JSON Schema 自动卡住
- **一键脚手架** — `make new-node NAME=foo` 生成命名空间 / include 全对齐的三层骨架
- **无 ROS 也能校验** — `make validate-all` 数秒跑完，schema / 一致性 / 分层 / 命名全覆盖

## 快速开始

```bash
pip install pyyaml jsonschema
make validate-all          # 本地校验，无需 ROS2
```

环境搭建、构建、运行见 [新人上手](docs/onboarding.md)。

## 创建包

```bash
make new-node    NAME=robot_foo   # C++ 节点
make new-node-py NAME=robot_foo   # Python 节点
make new-lib     NAME=robot_foo   # 纯 C++ 库
make new-msgs    NAME=robot_foo   # 消息定义
make new-bringup NAME=robot_foo   # 集成 launch 包
```

包名 == 命名空间 == include 目录，三者必须一致（脚手架已保证）。

## 文档

| 文档 | 内容 |
|------|------|
| [新人上手](docs/onboarding.md) | 从 0 到跑起来 |
| [系统架构](docs/architecture.md) | 包依赖、数据流、分层 |
| [开发规范](docs/conventions.md) | 命名、分层、契约（硬约定） |
| [经验传承](docs/lessons_learned.md) | 踩坑与决策的"为什么" |
| [硬件清单](docs/hardware.md) | 部件与接线 |

## 许可证

MIT
