// ═══════════════════════════════════════════════════════════
//  Model 层：控制包的纯 C++ 数据结构（零 ROS2 依赖）
// ═══════════════════════════════════════════════════════════
#pragma once

#include <vector>

namespace robot_control::model {

/// 单个威胁（相对机器人坐标系）
struct Threat {
    double distance = 0.0;  // m
    double bearing = 0.0;   // rad，正=左，负=右
};

/// 速度指令
struct TwistCmd {
    double linear = 0.0;   // m/s
    double angular = 0.0;  // rad/s
};

/// 运行时配置
struct Config {
    double target_linear_speed = 0.5;  // m/s 无威胁时的期望前进速度
    double max_angular_speed = 1.5;    // rad/s 避障转向角速度
    double safe_distance = 0.8;        // m，开始触发避障的距离
};

}  // namespace robot_control::model
