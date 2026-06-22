// ═══ PID 控制器测试 ═══
#include <gtest/gtest.h>

#include "robot_common/pid.hpp"

using robot_common::PIDController;

TEST(PIDTest, PureProportional) {
    PIDController pid({1.0, 0.0, 0.0}, -10.0, 10.0);
    double out = pid.calculate(1.0, 0.0, 0.1);
    EXPECT_NEAR(out, 1.0, 1e-9);
}

TEST(PIDTest, OutputClamping) {
    PIDController pid({100.0, 0.0, 0.0}, -5.0, 5.0);
    double out = pid.calculate(1.0, 0.0, 0.1);
    EXPECT_DOUBLE_EQ(out, 5.0);  // kp=100 * error=1 → 钳位到 5
}

TEST(PIDTest, IntegralAntiWindup) {
    PIDController pid({0.0, 10.0, 0.0}, -5.0, 5.0);
    // 持续正误差，输出被限幅，积分项应被撤销
    pid.calculate(10.0, 0.0, 0.1);
    pid.calculate(10.0, 0.0, 0.1);
    pid.calculate(10.0, 0.0, 0.1);
    // 若无抗饱和，积分会持续增长导致输出远超 5
    double out = pid.calculate(10.0, 0.0, 0.1);
    EXPECT_DOUBLE_EQ(out, 5.0);
}

TEST(PIDTest, ResetClearsState) {
    PIDController pid({0.0, 10.0, 0.0}, -100.0, 100.0);
    pid.calculate(1.0, 0.0, 0.1);
    pid.reset();
    // reset 后第一个微分项应为 0
    double out = pid.calculate(1.0, 0.0, 0.1);
    EXPECT_NEAR(out, 1.0, 1e-9);  // 仅积分 = ki * error * dt = 10 * 1 * 0.1
}

TEST(PIDTest, NegativeDtThrows) {
    PIDController pid({1.0, 0.0, 0.0}, -10.0, 10.0);
    EXPECT_THROW(pid.calculate(1.0, 0.0, 0.0), std::invalid_argument);
    EXPECT_THROW(pid.calculate(1.0, 0.0, -0.1), std::invalid_argument);
}
