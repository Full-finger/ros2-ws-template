// ═══════════════════════════════════════════════════════════
//  Service 层：安全速度计算（纯逻辑，零 ROS2 依赖）
//
//  避障策略：
//   - 用 robot_common::PID 把"与最近威胁的距离"维持为 safe_distance
//   - PID 输出 [0,1] 作为制动因子 braking
//   - linear = target * (1 - braking)
//   - angular = 朝远离最近威胁方向转向 × max_angular_speed × braking
//
//  这是 header-only：含 PID 集成逻辑，便于阅读。
// ═══════════════════════════════════════════════════════════
#pragma once

#include <algorithm>
#include <cmath>

#include "robot_common/pid.hpp"
#include "robot_control/model/types.hpp"
#include "robot_control/model/errors.hpp"

namespace robot_control::service {

class SafetyVelocityService {
public:
    explicit SafetyVelocityService(const model::Config &config)
        : config_(config),
          braking_pid_({config.kp, config.ki, config.kd}, 0.0, 1.0) {}

    /// 计算安全速度指令
    /// @param threats 当前威胁列表（来自感知层）
    /// @param dt      距上次调用的时间步（秒）
    model::TwistCmd compute(const std::vector<model::Threat> &threats,
                            double dt) {
        if (dt <= 0.0) {
            throw model::ControlError("dt 必须为正");
        }

        const auto *nearest = find_nearest(threats);
        const double min_dist = nearest ? nearest->distance
                                        : config_.safe_distance + 1.0;

        // 制动因子：setpoint=safe_distance, measurement=min_dist
        // 当 min_dist < safe_distance，error>0，braking 趋向 1（全制动）
        const double braking = braking_pid_.calculate(
            config_.safe_distance, min_dist, dt);

        model::TwistCmd cmd;
        cmd.linear = std::clamp(
            config_.target_linear_speed * (1.0 - braking),
            -config_.max_linear_speed, config_.max_linear_speed);

        if (nearest && braking > 0.0 && min_dist < config_.safe_distance) {
            // 朝远离威胁方向转向：威胁在左(bearing>0)→向右转(angular<0)
            const double dir = (nearest->bearing >= 0.0) ? -1.0 : 1.0;
            cmd.angular = dir * config_.max_angular_speed * braking;
        }

        return cmd;
    }

    void update_config(const model::Config &config) {
        config_ = config;
        braking_pid_.set_gains({config.kp, config.ki, config.kd});
    }

    void reset() { braking_pid_.reset(); }

    [[nodiscard]] const model::Config &config() const { return config_; }

private:
    static const model::Threat *find_nearest(
        const std::vector<model::Threat> &threats) {
        const model::Threat *best = nullptr;
        for (const auto &t : threats) {
            if (!best || t.distance < best->distance) {
                best = &t;
            }
        }
        return best;
    }

    model::Config config_;
    robot_common::PIDController braking_pid_;
};

}  // namespace robot_control::service
