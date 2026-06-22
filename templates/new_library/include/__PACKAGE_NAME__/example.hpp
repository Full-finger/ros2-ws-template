// ═══════════════════════════════════════════════════════════
//  纯 C++ 工具库示例（死区滤波器）
//  - 零 ROS2 依赖，仅 STL
// ═══════════════════════════════════════════════════════════
#pragma once

namespace __PACKAGE_NAME__ {

/// 死区滤波器：绝对值小于阈值的输入归零
class Deadzone {
public:
    explicit Deadzone(double threshold);
    double apply(double value) const;

private:
    double threshold_;
};

}  // namespace __PACKAGE_NAME__
