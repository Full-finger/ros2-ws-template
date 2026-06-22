// ═══════════════════════════════════════════════════════════
//  Service 层：差速驱动运动学（纯逻辑，零 ROS2 依赖）
//
//  给定左右轮线速度，按差速驱动模型积分得到里程计：
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
#include "robot_hardware/model/types.hpp"
#include "robot_hardware/model/errors.hpp"

namespace robot_hardware::service {

class DifferentialDriveService {
public:
    explicit DifferentialDriveService(const model::Config &config)
        : config_(config) {}

    /// 单步里程计更新
    /// @throws model::SensorReadError 若轮速读数非法（NaN 等）
    model::OdometryData update_odometry(const model::MotorReading &reading,
                                        double dt) {
        validate(reading);
        if (dt <= 0.0) {
            throw model::SensorReadError("dt 必须为正");
        }

        const double v = (reading.left_velocity + reading.right_velocity) / 2.0;
        const double w =
            (reading.right_velocity - reading.left_velocity) / config_.wheel_base;

        odom_.theta = robot_common::math::wrap_angle(odom_.theta + w * dt);
        odom_.x += v * std::cos(odom_.theta) * dt;
        odom_.y += v * std::sin(odom_.theta) * dt;
        odom_.linear_velocity = v;
        odom_.angular_velocity = w;
        odom_.timestamp = reading.timestamp;

        return odom_;
    }

    void update_config(const model::Config &config) { config_ = config; }

    void reset() {
        odom_ = {};
    }

    [[nodiscard]] const model::OdometryData &odom() const { return odom_; }
    [[nodiscard]] const model::Config &config() const { return config_; }

private:
    static void validate(const model::MotorReading &reading) {
        if (std::isnan(reading.left_velocity) || std::isnan(reading.right_velocity)) {
            throw model::SensorReadError("电机读数含 NaN");
        }
    }

    model::Config config_;
    model::OdometryData odom_{};
};

}  // namespace robot_hardware::service
