// ═══════════════════════════════════════════════════════════
//  Model 层：硬件异常类型
// ═══════════════════════════════════════════════════════════
#pragma once

#include <stdexcept>

namespace robot_hardware::model {

class HardwareError : public std::runtime_error {
public:
    explicit HardwareError(const std::string& msg) : std::runtime_error(msg) {}
};

class SensorReadError : public HardwareError {
public:
    explicit SensorReadError(const std::string& msg) : HardwareError(msg) {}
};

/// 配置非法（如 wheel_base <= 0）。配置错误是硬件层故障的根因之一，单独成类
/// 便于调用方区分“传感器读数异常”与“参数配错”。
class ConfigError : public HardwareError {
public:
    explicit ConfigError(const std::string& msg) : HardwareError(msg) {}
};

}  // namespace robot_hardware::model
