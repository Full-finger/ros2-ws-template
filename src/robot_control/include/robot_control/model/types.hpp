// ═══════════════════════════════════════════════════════════
//  Model 层：控制包的纯 C++ 数据结构（零 ROS2 依赖）
// ═══════════════════════════════════════════════════════════
#pragma once

#include <vector>

namespace robot_control::model {

/// 单个威胁（相对机器人坐标系）
struct Threat {
    double distance = 0.0;   // m
    double bearing = 0.0;    // rad，正=左，负=右
    int severity = 0;        // 0~100
};

/// 速度指令
struct TwistCmd {
    double linear = 0.0;   // m/s
    double angular = 0.0;  // rad/s
};

/// 运行时配置
struct Config {
    double target_linear_speed = 0.5;   // m/s 期望前进速度
    double max_linear_speed = 1.0;      // m/s
    double max_angular_speed = 1.5;     // rad/s
    double safe_distance = 0.8;         // m，开始避障的距离
    double kp = 2.0;                    // 制动 PID 增益
    double ki = 0.5;
    double kd = 0.1;
};

}  // namespace robot_control::model
