// ═══════════════════════════════════════════════════════════
//  Model 层：控制异常
// ═══════════════════════════════════════════════════════════
#pragma once

#include <stdexcept>

namespace robot_control::model {

class ControlError : public std::runtime_error {
public:
    explicit ControlError(const std::string& msg) : std::runtime_error(msg) {}
};

}  // namespace robot_control::model
