// ═══ 纯 C++ 测试 ═══
#include <gtest/gtest.h>

#include "__PACKAGE_NAME__/example.hpp"

using namespace __PACKAGE_NAME__;

TEST(DeadzoneTest, BelowThresholdReturnsZero) {
    Deadzone dz(0.5);
    EXPECT_DOUBLE_EQ(dz.apply(0.3), 0.0);
    EXPECT_DOUBLE_EQ(dz.apply(-0.3), 0.0);
}

TEST(DeadzoneTest, AboveThresholdPassesThrough) {
    Deadzone dz(0.5);
    EXPECT_DOUBLE_EQ(dz.apply(0.8), 0.8);
    EXPECT_DOUBLE_EQ(dz.apply(-0.8), -0.8);
}

TEST(DeadzoneTest, ExactBoundaryReturnsZero) {
    Deadzone dz(0.5);
    // < threshold，边界值归零
    EXPECT_DOUBLE_EQ(dz.apply(0.5), 0.0);
}
