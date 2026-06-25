// ═══════════════════════════════════════════════════════════
//  数学工具（header-only，零 ROS2 依赖）
// ═══════════════════════════════════════════════════════════
#pragma once

#include <algorithm>
#include <cmath>

namespace robot_common::math {

/// 将角度归一化到 [-pi, pi]
inline double wrap_angle(double angle) {
    constexpr double TWO_PI = 2.0 * M_PI;
    double a = std::fmod(angle + M_PI, TWO_PI);
    if (a < 0.0)
        a += TWO_PI;
    return a - M_PI;
}

/// 线性插值
inline double lerp(double a, double b, double t) {
    return a + (b - a) * t;
}

/// 死区：绝对值小于 threshold 归零
inline double deadzone(double value, double threshold) {
    return std::abs(value) < threshold ? 0.0 : value;
}

}  // namespace robot_common::math
