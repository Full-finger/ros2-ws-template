// ═══ 数学工具测试 ═══
#include <gtest/gtest.h>

#include "robot_common/math_utils.hpp"

using namespace robot_common::math;

TEST(MathUtilsTest, WrapAngle) {
    EXPECT_NEAR(wrap_angle(0.0), 0.0, 1e-9);
    // wrap_angle 的值域是 [-π, π]，端点闭合在 -π：
    // +π 与 -π 是同一朝向，本实现统一归一化到 -π。
    EXPECT_NEAR(wrap_angle(M_PI), -M_PI, 1e-9);
    EXPECT_NEAR(wrap_angle(-M_PI), -M_PI, 1e-9);
    EXPECT_NEAR(wrap_angle(3.0 * M_PI), -M_PI, 1e-9);
    EXPECT_NEAR(wrap_angle(5.0 * M_PI), -M_PI, 1e-9);
    EXPECT_NEAR(wrap_angle(-5.0 * M_PI), -M_PI, 1e-9);
    // 边界内仍取正
    EXPECT_NEAR(wrap_angle(M_PI - 0.01), M_PI - 0.01, 1e-9);
}

TEST(MathUtilsTest, Lerp) {
    EXPECT_NEAR(lerp(0.0, 10.0, 0.0), 0.0, 1e-9);
    EXPECT_NEAR(lerp(0.0, 10.0, 1.0), 10.0, 1e-9);
    EXPECT_NEAR(lerp(0.0, 10.0, 0.5), 5.0, 1e-9);
}

TEST(MathUtilsTest, Deadzone) {
    EXPECT_DOUBLE_EQ(deadzone(0.3, 0.5), 0.0);
    EXPECT_DOUBLE_EQ(deadzone(-0.3, 0.5), 0.0);
    EXPECT_DOUBLE_EQ(deadzone(0.8, 0.5), 0.8);
    EXPECT_DOUBLE_EQ(deadzone(-0.8, 0.5), -0.8);
}
