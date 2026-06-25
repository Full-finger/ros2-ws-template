// ═══════════════════════════════════════════════════════════
//  PID 控制器（纯 C++，零 ROS2 依赖）
//  - 带积分抗饱和（integral clamping）
//  - 可热更新增益
// ═══════════════════════════════════════════════════════════
#pragma once

namespace robot_common {

class PIDController {
public:
    struct Gains {
        double kp = 0.0;
        double ki = 0.0;
        double kd = 0.0;
    };

    PIDController(Gains gains, double output_min, double output_max);

    /// 单步计算
    /// @param setpoint  目标值
    /// @param measurement 当前测量值
    /// @param dt        时间步长（秒），必须 > 0
    double calculate(double setpoint, double measurement, double dt);

    /// 更新增益（热更新）
    void set_gains(const Gains& gains) { gains_ = gains; }

    /// 清零内部状态（积分项、微分项）
    void reset();

    [[nodiscard]] Gains gains() const { return gains_; }

private:
    Gains gains_;
    double output_min_;
    double output_max_;
    double integral_ = 0.0;
    double last_error_ = 0.0;
    bool first_ = true;
};

}  // namespace robot_common
