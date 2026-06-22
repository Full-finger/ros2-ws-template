// ═══════════════════════════════════════════════════════════
//  Model 层：纯数据结构
//  - 零 ROS2 依赖
//  - 零业务逻辑
//  - 只描述"是什么"
// ═══════════════════════════════════════════════════════════
#pragma once

namespace __PACKAGE_NAME__::model {

/// 输入数据（对应 ROS2 输入消息的业务语义）
struct InputData {
    double value;
    double timestamp;
};

/// 输出数据（对应 ROS2 输出消息的业务语义）
struct OutputData {
    double result;
    bool valid;
};

/// 运行时配置（对应 YAML 中的参数，但不依赖 rclcpp）
struct Config {
    double update_rate = 10.0;   // Hz
    double threshold = 0.5;
    bool debug = false;
};

}  // namespace __PACKAGE_NAME__::model
