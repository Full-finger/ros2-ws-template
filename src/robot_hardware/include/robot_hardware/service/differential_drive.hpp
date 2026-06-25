// ═══════════════════════════════════════════════════════════
//  Service 层：差速驱动运动学（纯逻辑，零 ROS2 依赖）
//
//  给定左右轮角速度（rad/s），按差速驱动模型积分得到里程计：
//    v_left  = left_wheel_speed  * wheel_radius
//    v_right = right_wheel_speed * wheel_radius
//    v   = (v_left + v_right) / 2
//    w   = (v_right - v_left) / wheel_base
//    x  += v * cos(theta) * dt
//    y  += v * sin(theta) * dt
//    theta = wrap_angle(theta + w * dt)
//
//  header-only：逻辑简单且含运动学公式，适合内联阅读。
// ═══════════════════════════════════════════════════════════
#pragma once

#include <cmath>

#include "robot_common/math_utils.hpp"
#include "robot_hardware/model/errors.hpp"
#include "robot_hardware/model/types.hpp"

namespace robot_hardware::service {

class DifferentialDriveService {
public:
    explicit DifferentialDriveService(const model::Config& config) : config_(config) {
        validate_config(config_);
    }

    /// 单步里程计更新
    /// @throws model::SensorReadError 若轮速读数非法（NaN 等）
    model::OdometryData update_odometry(const model::MotorReading& reading, double dt) {
        validate(reading);
        if (dt <= 0.0) {
            throw model::SensorReadError("dt 必须为正");
        }

        const double v_left = reading.left_wheel_speed * config_.wheel_radius;
        const double v_right = reading.right_wheel_speed * config_.wheel_radius;
        const double v = (v_left + v_right) / 2.0;
        const double w = (v_right - v_left) / config_.wheel_base;

        odom_.theta = robot_common::math::wrap_angle(odom_.theta + w * dt);
        odom_.x += v * std::cos(odom_.theta) * dt;
        odom_.y += v * std::sin(odom_.theta) * dt;
        odom_.linear_velocity = v;
        odom_.angular_velocity = w;
        odom_.timestamp = reading.timestamp;

        return odom_;
    }

    void update_config(const model::Config& config) {
        validate_config(config);
        config_ = config;
    }

    void reset() { odom_ = {}; }

    [[nodiscard]] const model::OdometryData& odom() const { return odom_; }
    [[nodiscard]] const model::Config& config() const { return config_; }

private:
    // 用 !(x > 0.0) 而非 x <= 0.0：这样 NaN 也会被拦下
    // （NaN > 0 为假 → !假 = 真 → 抛错），避免 NaN 配置静默通过。
    static void validate_config(const model::Config& c) {
        if (!(c.wheel_base > 0.0)) {
            throw model::ConfigError("wheel_base 必须为正");
        }
        if (!(c.wheel_radius > 0.0)) {
            throw model::ConfigError("wheel_radius 必须为正");
        }
    }

    static void validate(const model::MotorReading& reading) {
        if (!std::isfinite(reading.left_wheel_speed) || !std::isfinite(reading.right_wheel_speed)) {
            throw model::SensorReadError("电机读数含 NaN 或 Inf");
        }
    }

    model::Config config_;
    model::OdometryData odom_{};
};

}  // namespace robot_hardware::service
