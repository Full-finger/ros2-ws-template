// ═══════════════════════════════════════════════════════════
//  Model 层：硬件异常类型
// ═══════════════════════════════════════════════════════════
#pragma once

#include <stdexcept>

namespace robot_hardware::model {

class HardwareError : public std::runtime_error {
public:
    explicit HardwareError(const std::string &msg) : std::runtime_error(msg) {}
};

class SensorReadError : public HardwareError {
public:
    explicit SensorReadError(const std::string &msg) : HardwareError(msg) {}
};

}  // namespace robot_hardware::model
