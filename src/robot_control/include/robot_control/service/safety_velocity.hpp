// ═══════════════════════════════════════════════════════════
//  Service 层：安全速度（纯逻辑，零 ROS2 依赖）
//
//  避障策略（一眼懂的 if/else）：
//   - 无威胁，或最近威胁仍在 safe_distance 之外：保持目标速度直行
//   - 有威胁进入 safe_distance：立即停车，朝远离最近威胁的方向转向
//
//  转向方向：威胁在左 (bearing >= 0) → 向右转 (angular < 0)；反之向左转。
//  这是 header-only：逻辑简单，便于阅读。
// ═══════════════════════════════════════════════════════════
#pragma once

#include <cmath>
#include <vector>

#include "robot_control/model/errors.hpp"
#include "robot_control/model/types.hpp"

namespace robot_control::service {

class SafetyVelocityService {
public:
    explicit SafetyVelocityService(const model::Config& config) : config_(config) {}

    /// 障碍物笛卡尔坐标 → 威胁极坐标（distance/bearing）。
    /// 坐标变换是 service 的业务逻辑，controller 不应直接做几何运算。
    static model::Threat to_threat(double x, double y) {
        return model::Threat{
            .distance = std::hypot(x, y),
            .bearing = std::atan2(y, x),
        };
    }

    /// 计算安全速度指令
    /// @param threats 当前威胁列表（来自感知层）
    /// @param dt      距上次调用的时间步（秒）；仅用于校验调用节律
    model::TwistCmd compute(const std::vector<model::Threat>& threats, double dt) {
        if (dt <= 0.0) {
            throw model::ControlError("dt 必须为正");
        }

        const auto* nearest = find_nearest(threats);
        const bool safe = !nearest || nearest->distance >= config_.safe_distance;
        if (safe) {
            return {config_.target_linear_speed, 0.0};
        }

        // 威胁在左 (bearing >= 0) → 向右转 (angular < 0)；反之向左转
        const double dir = (nearest->bearing >= 0.0) ? -1.0 : 1.0;
        return {0.0, dir * config_.max_angular_speed};
    }

    void update_config(const model::Config& config) { config_ = config; }

    [[nodiscard]] const model::Config& config() const { return config_; }

private:
    static const model::Threat* find_nearest(const std::vector<model::Threat>& threats) {
        const model::Threat* best = nullptr;
        for (const auto& t : threats) {
            if (!best || t.distance < best->distance) {
                best = &t;
            }
        }
        return best;
    }

    model::Config config_;
};

}  // namespace robot_control::service
