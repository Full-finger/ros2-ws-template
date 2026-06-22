// ═══════════════════════════════════════════════════════════
//  Model 层：感知异常
// ═══════════════════════════════════════════════════════════
#pragma once

#include <stdexcept>

namespace robot_perception::model {

class PerceptionError : public std::runtime_error {
public:
    explicit PerceptionError(const std::string &msg) : std::runtime_error(msg) {}
};

}  // namespace robot_perception::model
