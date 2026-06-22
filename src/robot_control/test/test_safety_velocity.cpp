// ═══ 安全速度计算测试（纯逻辑） ═══
#include <gtest/gtest.h>

#include "robot_control/model/types.hpp"
#include "robot_control/service/safety_velocity.hpp"

using robot_control::model::Config;
using robot_control::model::Threat;
using robot_control::model::TwistCmd;
using robot_control::service::SafetyVelocityService;

class SafetyVelocityTest : public ::testing::Test {
protected:
    void SetUp() override {
        Config config;
        config.target_linear_speed = 0.5;
        config.max_linear_speed = 1.0;
        config.max_angular_speed = 1.5;
        config.safe_distance = 0.8;
        config.kp = 2.0;
        config.ki = 0.5;
        config.kd = 0.1;
        svc_ = std::make_unique<SafetyVelocityService>(config);
    }
    std::unique_ptr<SafetyVelocityService> svc_;
    const double dt = 0.1;
};

TEST_F(SafetyVelocityTest, NoThreatFullSpeed) {
    TwistCmd cmd = svc_->compute({}, dt);
    // 无威胁：error = safe - (safe+1) < 0，braking 钳到 0，全速
    EXPECT_NEAR(cmd.linear, 0.5, 1e-9);
    EXPECT_NEAR(cmd.angular, 0.0, 1e-9);
}

TEST_F(SafetyVelocityTest, FarThreatFullSpeed) {
    Threat t{.distance = 2.0, .bearing = 0.0};  // 远超 safe_distance
    TwistCmd cmd = svc_->compute({t}, dt);
    EXPECT_NEAR(cmd.linear, 0.5, 1e-9);
}

TEST_F(SafetyVelocityTest, FrontalThreatSlowsDown) {
    Threat t{.distance = 0.3, .bearing = 0.0};  // 正前方，很近
    TwistCmd cmd = svc_->compute({t}, dt);
    EXPECT_LT(cmd.linear, 0.5);  // 减速了
    // bearing=0 走 >=0 分支，向右转（angular<=0）
    EXPECT_LE(cmd.angular, 0.0);
}

TEST_F(SafetyVelocityTest, LeftThreatTurnsRight) {
    Threat t{.distance = 0.3, .bearing = 0.5};  // 左前方
    TwistCmd cmd = svc_->compute({t}, dt);
    EXPECT_LT(cmd.angular, 0.0);  // 向右转（angular<0）
}

TEST_F(SafetyVelocityTest, RightThreatTurnsLeft) {
    Threat t{.distance = 0.3, .bearing = -0.5};  // 右前方
    TwistCmd cmd = svc_->compute({t}, dt);
    EXPECT_GT(cmd.angular, 0.0);  // 向左转
}

TEST_F(SafetyVelocityTest, NearestThreatDominates) {
    Threat far{.distance = 1.5, .bearing = 0.0};
    Threat near{.distance = 0.3, .bearing = -0.5};
    TwistCmd cmd = svc_->compute({far, near}, dt);
    EXPECT_GT(cmd.angular, 0.0);  // 取最近的 near（右侧），向左转
}

TEST_F(SafetyVelocityTest, NonPositiveDtThrows) {
    Threat t{.distance = 0.3, .bearing = 0.0};
    EXPECT_THROW(svc_->compute({t}, 0.0), robot_control::model::ControlError);
    EXPECT_THROW(svc_->compute({t}, -0.1), robot_control::model::ControlError);
}
