# 开发规范

> 这份是硬性约定，`make validate-all` 会机器校验其中大部分；剩下的靠 code review。

## 命名

### 包名 == C++ 命名空间 == include 目录

三者必须完全一致，由脚手架 `make new-*` 保证：

```
包名          robot_control
命名空间      robot_control::model / ::service / ::controller
include 路径  src/robot_control/include/robot_control/...
头文件引用    #include "robot_control/model/types.hpp"
plugin.yaml   runtime.node: "robot_control::controller::MainNode"
```

规则：小写字母开头，只含 `[a-z0-9_]`。

### Topic 命名

- 风格：`snake_case`
- 私有 topic 用 `~/` 前缀，第一段必须落在语义前缀里：`input` / `output` / `status` / `cmd` / `debug`
- 深度至少 2 段：`~/output/odom` ✓，`~/foo` ✗（太浅）
- 禁用词：`temp` `data` `tmp` `foo` `bar` `new` `test` `xxx`
- 禁用模式：双斜杠 `//`、末尾斜杠

规则集见 `schemas/topic_naming.json`，由 `make validate-topics` 校验。

### C++

- namespace 与文件路径对应：`robot_control/service/safety_velocity.hpp` → `robot_control::service::SafetyVelocityService`
- 类名 `PascalCase`，函数/变量 `snake_case`，成员变量带尾下划线 `config_`
- 显式 include **所有**用到的头文件，不依赖传递 include（`rclcpp.hpp` 不会替你带 `set_parameters_result.hpp`）

## 分层职责

| 层 | 允许的 #include | 禁止 |
|----|-----------------|------|
| `model` | 仅 STL | 任何业务逻辑、ROS2 |
| `service` | STL + `model/` + `robot_common` | 任何 `rclcpp/*`、`*_msgs/*` |
| `controller` | 任意，但需显式 | 业务逻辑（只能调 service） |

**判定标准**：把 `controller` 整个删掉，`service` 能不能编译并通过 gtest？能 → 合格。

### service 何时拆 .cpp

- header-only：实现 < 200 行，或纯模板/内联（参考 `robot_common` 的数学工具、各 node 的 service）
- 拆 .cpp：实现 > 200 行或含重算法，声明留 `include/<pkg>/service/`，实现进 `src/service/`，CMake `add_library(${PROJECT_NAME}_service ...)` 加进去

## plugin.yaml 契约

每个包**必须**有 `plugin.yaml`，`type` 字段决定必填项：

| type | 必填 | 示例包 |
|------|------|--------|
| `library` | `exposes.headers` | `robot_common` |
| `node` | `runtime.node` | `robot_hardware` |
| `messages` | `interfaces.{msg,srv,action}` | `robot_msgs` |
| `bringup` | `subpackages`（≥1） | `robot_bringup` |

- 元信息（name/version/maintainer/license）**只在 `package.xml`**，`plugin.yaml` 不重复。
- `depends_on` 列运行时依赖的本项目包，必须 ⊆ `package.xml` 的 `<depend>`。
- 参数的 `default` 类型必须和 `type` 匹配（`double` 配数字、`string_array` 配字符串数组）。
- `config/*.yaml` 里的每个参数键必须被某个 node 包的 `plugin.yaml` 声明过
  ——防止参数名 typo / 大小写错 / 未声明导致 config 静默回退默认值
  （节点名允许与包名不同，按"全局声明并集"判定；`/**` 通配跳过）。
- 校验：`make validate-schema` + `make validate-cross`。

## Git 与提交

- 格式化：`clang-format`（`.clang-format` 已配，Google 基础 + 100 列 + 4 空格缩进）
- pre-commit：`pre-commit install` 后提交自动跑 schema/yaml/格式校验
- 提交信息建议 Conventional Commits：`feat:` `fix:` `docs:` `refactor:` `test:`
- 分支：`main` 稳定，`develop` 集成，feature 分支 `feat/<短描述>`

## 测试

- **service 层必须有 gtest**——这是拆三层的全部意义。
- controller 层不强求单测（ROS2 集成测试成本高），靠 `colcon test` 的集成验证。
- 测试文件放 `test/`，命名 `test_<被测对象>.cpp`，链接 `${PROJECT_NAME}` 或 `ament_target_dependencies`。

## CMake

- 业务包的 service 若 header-only，主 target 只编译 `src/main_node.cpp`。
- 用 `ament_target_dependencies(target dep1 dep2)` 引入 ROS2 依赖，别手写 `target_link_libraries(... rclcpp::rclcpp)`。
- `install` 三件套：可执行文件 → `lib/<pkg>`，头文件 → `include`，launch/config → `share/<pkg>`。
