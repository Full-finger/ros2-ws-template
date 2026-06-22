// ═══════════════════════════════════════════════════════════
//  Model 层：异常类型
// ═══════════════════════════════════════════════════════════
#pragma once

#include <stdexcept>

namespace __PACKAGE_NAME__::model {

/// 输入校验失败（可恢复，Controller 层转 WARN 日志）
class InputValidationError : public std::runtime_error {
public:
    explicit InputValidationError(const std::string &msg)
        : std::runtime_error(msg) {}
};

/// 处理异常（不可恢复，Controller 层转 ERROR 日志）
class ProcessingError : public std::runtime_error {
public:
    explicit ProcessingError(const std::string &msg)
        : std::runtime_error(msg) {}
};

}  // namespace __PACKAGE_NAME__::model
