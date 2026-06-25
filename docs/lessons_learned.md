# 经验传承（Lessons Learned）

> **这是全仓最重要的文档。** 每踩一个新坑，请回来补一条。知识不落文档，换届即清零。

---

## 核心设计决策及其"为什么"

### 1. 为什么要把包拆成 model / service / controller 三层？

**痛点（真实发生过）**：早期把算法和 ROS2 调用写在一个节点里，结果：
- 算法没法单测，只能靠"跑起来肉眼看"
- 升级 ROS2（Foxy → Galactic → Humble）时，rclcpp API 变动牵连算法重写
- 换个人接手，看不懂哪段是逻辑、哪段是框架胶水

**三层拆分后的收益**：
- `service` 层是纯 C++，`colcon test` 里用 gtest 直接打，不启动任何 ROS2 节点
- 算法在 CI 上秒级回归，硬件没到也能验证逻辑
- `controller` 层很薄，换 ROS2 发行版只改这一层

**判定标准（写代码时反复自问）**：把 `controller` 整个删掉，`service` 能不能独立编译并通过测试？不能 → 你把逻辑写错地方了。

### 2. 为什么 robot_common 要零 ROS2 依赖？

曾经让 `robot_common` 用 `geometry_msgs::msg::Vector3`，觉得"反正都要装 ROS2"。后果：
- 所有依赖 `robot_common` 的包都被传染了 ROS2 头文件
- 算法层被迫 include `*_msgs`，无法裸测
- 一个纯数学工具库，编译要拉半个 ROS2

**现在的约定**：`robot_common` 自己定义纯 C++ 类型（`math::Vec3` 等），`controller` 层负责 `robot_common::xxx ↔ geometry_msgs::xxx` 的转换。多写几行转换代码，换回整个算法层的可测性。

### 3. 为什么 plugin.yaml 和 package.xml 要去重？

最初 `plugin.yaml` 也写 `name/version/maintainer`，结果两份元信息永远对不上，CI 报莫名其妙的错。

**现在**：元信息只在 `package.xml`，`plugin.yaml` 只管 ROS2 接口契约。`validate_cross.py` 交叉检查二者一致性（namespace 匹配、`depends_on` ⊆ `<depend>`）。

### 4. 为什么用 ament_cmake 而不是纯 cmake？

`robot_common` 是纯 C++，但放在 colcon workspace 里。用 ament_cmake 的好处：colcon 统一管理、`ament_cmake_gtest` 测试框架统一、install 路径自动处理。**用 ament_cmake ≠ 依赖 ROS2**——不 `find_package(rclcpp)` 就没有运行时依赖。

### 5. 为什么 bringup 不叫 metapackage？

ROS2 的 `metapackage` 有特定语义：只聚合 `<exec_depend>`、不构建任何东西（如 `ros-humble-navigation`）。我们的 `robot_bringup` 有 launch 文件和 config 要 install，是**集成包**，不是纯聚合。混用会导致 CMakeLists 和 package.xml 的写法不对。所以 `plugin.yaml` 的 type 用 `bringup`，`metapackage` 留给将来真·纯聚合包。

---

## 踩过的坑（每条都真实发生过）

### 构建系统

- **JSON Schema 的 `additionalProperties: false` + `allOf` 不协作**：根级 `additionalProperties` 只看根的 `properties`，看不到 `allOf.then` 里引入的键。修法：把所有键都在根 `properties` 里声明（松定义），`allOf` 只管 `required`。
- **Makefile recipe 必须用 TAB**：4 空格会报 `missing separator`，Markdown 里粘贴常丢 tab。
- **占位符替换只改内容不重命名目录**：`__PACKAGE_NAME__` 出现在**目录名**（`include/__PACKAGE_NAME__/`）和**文件名**（`__PACKAGE_NAME__.launch.py`）里，光 `sed` 内容不够，必须 `mv` 重命名。`scripts/new_pkg.sh` 已处理。

### C++

- **隐式传递 include**：`#include <rclcpp/rclcpp.hpp>` 不会替你带 `set_parameters_result.hpp`，换版本就编译不过。**显式 include 所有用到的头文件**。
- **`10.0` 同时是 `number` 和 `integer`**：JSON Schema 的 `oneOf` 对 `10.0` 歧义，校验会误报。params schema 里合并成单个 `number`。

### 接口契约

- **topic 正则和私有命名空间**：`~/output/odom` 是合法 ROS2 私有 topic，但 `^/...` 的正则拒绝它。正则要写成 `^~?(/...)+$`。
- **parameter 的 default 与 type 不匹配**：`type: double` 却给 `default: "fast"`。schema 里用 `allOf` 的 `if/then` 按 type 校验 default 类型。
- **空 YAML 文件**：bringup 初始 config 全是注释，pyyaml 解析成 `None`，schema 期望 object 报错。校验脚本要跳过空文档。

### 流程

- **CI 跑了和本地不一样的工具**：本地用 python `jsonschema`，CI 用 `ajv`，draft-07 行为偶有差异。**两个都装、都跑**，保证一致。
- **pre-commit 配了 ≠ 真的在跑**：仓库有 `.pre-commit-config.yaml`，但没执行 `pre-commit install` 时提交根本不触发，black/flake8/clang-format 形同虚设，代码悄悄“格式漂移”直至 CI 红一片。**新人 clone 后第一件事**：`pre-commit install`，再 `pre-commit run --all-files` 全仓跑一遍。CI 只能兑底，本地不跑就晚了。
- **black / clang-format 跨大版本会改格式**：black 24 vs 26、clang-format 14 vs 18 的输出不一样。pre-commit、CI、本地三方**必须 pin 同一版本**（本仓 `black==24.8.0`、`clang-format==18.1.8`，CI 用 `pip install` 固定而非 `apt`），否则 CI 绿、本地红，或反过来，互相打架。

---

## 历届常见错误（新人必看）

1. **业务逻辑写进 controller**：订阅回调里写算法。→ 移到 `service`。
2. **service 层 include 了 `*_msgs`**：→ 用 `model` 类型，转换留 controller。
3. **新建包不跑 `make validate-all`**：→ CI 红，还不知道哪错。
4. **`depends_on` 漏写**：→ 拓扑序错，colcon 构建顺序乱，偶发编译失败。
5. **改了 `package.xml` 忘改 `plugin.yaml`**（或反之）：→ `validate_cross` 报不一致。
6. **lifecycle 节点不实现状态机**：→ 声明了 `lifecycle: true` 却用普通 `Node`。要用 `rclcpp_lifecycle::LifecycleNode`。
7. **在 `model` 层加 `#include <rclcpp/...>`**：→ model 不再可裸测。

---

## 升级 ROS2 发行版 Checklist

- [ ] 改 `.github/workflows/ci.yml` 的 `ROS_DISTRO` 和 base image
- [ ] `rosdep install` 看有无新缺失依赖
- [ ] 只需改 `controller` 层（rclcpp API 变动）；`service` 层理论上零改动
- [ ] 跑 `colcon test` 全绿
- [ ] 检查 `plugin.yaml` 的消息类型字符串是否仍有效

---

## 给下一届的话

- **文档 > 记忆**。你觉得"这很明显下次还记得"的，三个月后就忘了。
- **校验 > 信任**。凡是能用 schema/脚本卡住的规则，就别靠人 review。
- **可测性 > 优雅**。能裸跑 gtest 的代码，比"看起来很酷"的代码值钱十倍。
- 踩了新坑，**立刻回来补一条**，别等"有空再说"。
