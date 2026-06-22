// ═══════════════════════════════════════════════════════════
//  Model 层：硬件包的纯 C++ 数据结构（零 ROS2 依赖）
// ═══════════════════════════════════════════════════════════
#pragma once

namespace robot_hardware::model {

/// 电机原始读数（来自串口/驱动器）
struct MotorReading {
    double left_velocity = 0.0;   // 左轮线速度 m/s
    double right_velocity = 0.0;  // 右轮线速度 m/s
    double timestamp = 0.0;       // 秒
};

/// 轮式里程计结果（机器人坐标系积分）
struct OdometryData {
    double x = 0.0;
    double y = 0.0;
    double theta = 0.0;            // 朝向 [-pi, pi]
    double linear_velocity = 0.0;  // m/s
    double angular_velocity = 0.0; // rad/s
    double timestamp = 0.0;
};

/// IMU 读数
struct ImuData {
    double ax = 0.0, ay = 0.0, az = 0.0;  // 加速度 m/s^2
    double gx = 0.0, gy = 0.0, gz = 0.0;  // 角速度 rad/s
    double timestamp = 0.0;
};

/// 运行时配置
struct Config {
    std::string serial_port = "/dev/ttyUSB0";
    int baud_rate = 115200;
    double wheel_radius = 0.05;  // m
    double wheel_base = 0.3;     // m（左右轮距）
    double update_rate = 50.0;   // Hz
};

}  // namespace robot_hardware::model
