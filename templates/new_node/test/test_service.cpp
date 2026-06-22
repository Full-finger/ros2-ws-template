// ═══ 纯 C++ 测试：不需要 ROS2，直接测试 Service 层 ═══
#include <gtest/gtest.h>

#include "__PACKAGE_NAME__/model/types.hpp"
#include "__PACKAGE_NAME__/service/example_service.hpp"

using namespace __PACKAGE_NAME__;

class ExampleServiceTest : public ::testing::Test {
protected:
    void SetUp() override {
        model::Config config;
        config.threshold = 0.5;
        service_ = std::make_unique<service::ExampleService>(config);
    }
    std::unique_ptr<service::ExampleService> service_;
};

TEST_F(ExampleServiceTest, NormalInput) {
    model::InputData input{.value = 2.0, .timestamp = 0.0};
    auto output = service_->process(input);
    EXPECT_NEAR(output.result, 1.0, 1e-6);
    EXPECT_TRUE(output.valid);
}

TEST_F(ExampleServiceTest, ZeroInput) {
    model::InputData input{.value = 0.0, .timestamp = 0.0};
    auto output = service_->process(input);
    EXPECT_NEAR(output.result, 0.0, 1e-6);
    EXPECT_FALSE(output.valid);
}

TEST_F(ExampleServiceTest, NegativeInputThrows) {
    model::InputData input{.value = -1.0, .timestamp = 0.0};
    EXPECT_THROW(service_->process(input), model::InputValidationError);
}

TEST_F(ExampleServiceTest, ConfigUpdate) {
    model::Config new_config;
    new_config.threshold = 2.0;
    service_->update_config(new_config);

    model::InputData input{.value = 3.0, .timestamp = 0.0};
    auto output = service_->process(input);
    EXPECT_NEAR(output.result, 6.0, 1e-6);
}
