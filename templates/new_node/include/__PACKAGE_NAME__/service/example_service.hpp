// ═══════════════════════════════════════════════════════════
//  Service 层：纯业务逻辑（header-only 示例）
//  - 零 ROS2 依赖
//  - 可以用 gtest 直接测试
//  - 输入 Model 类型，输出 Model 类型
//
//  约定：小型 service 走 header-only；当实现超过约 200 行或含
//  复杂算法时，拆成 .hpp 声明 + src/service/*.cpp 实现，并在
//  CMakeLists.txt 中 add_library(${PROJECT_NAME}_service ...)。
// ═══════════════════════════════════════════════════════════
#pragma once

#include "__PACKAGE_NAME__/model/types.hpp"
#include "__PACKAGE_NAME__/model/errors.hpp"

namespace __PACKAGE_NAME__::service {

class ExampleService {
public:
    explicit ExampleService(const model::Config &config)
        : config_(config) {}

    /// 核心处理逻辑
    model::OutputData process(const model::InputData &input) {
        if (input.value < 0) {
            throw model::InputValidationError("输入值不能为负");
        }

        model::OutputData output;
        output.result = input.value * config_.threshold;
        output.valid = (output.result > 0.01);
        return output;
    }

    /// 热更新配置
    void update_config(const model::Config &config) { config_ = config; }

    [[nodiscard]] const model::Config &config() const { return config_; }

private:
    model::Config config_;
};

}  // namespace __PACKAGE_NAME__::service
