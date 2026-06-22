#include "robot_common/pid.hpp"

#include <algorithm>
#include <stdexcept>

namespace robot_common {

PIDController::PIDController(Gains gains, double output_min, double output_max)
    : gains_(gains), output_min_(output_min), output_max_(output_max) {}

double PIDController::calculate(double setpoint, double measurement, double dt) {
    if (dt <= 0.0) {
        throw std::invalid_argument("dt must be positive");
    }

    const double error = setpoint - measurement;

    // 积分项（累加前不钳位，输出时再抗饱和）
    integral_ += error * dt;

    // 微分项
    double derivative = 0.0;
    if (!first_) {
        derivative = (error - last_error_) / dt;
    }
    first_ = false;
    last_error_ = error;

    // 原始输出
    double output = gains_.kp * error
                  + gains_.ki * integral_
                  + gains_.kd * derivative;

    // 输出钳位 + 积分抗饱和：若输出已被限幅，撤销本次积分累加
    double clamped = std::clamp(output, output_min_, output_max_);
    if (clamped != output) {
        integral_ -= error * dt;  // 撤销
    }
    return clamped;
}

void PIDController::reset() {
    integral_ = 0.0;
    last_error_ = 0.0;
    first_ = true;
}

}  // namespace robot_common
