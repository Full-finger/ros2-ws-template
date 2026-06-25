// ═══════════════════════════════════════════════════════════
//  Controller 层：ROS2 适配
//  - timer 驱动周期性"读取电机"（此处模拟，真实环境接串口）
//  - 调 DifferentialDriveService 计算里程计
//  - model 类型 ↔ ROS 消息转换
//  - 提供 EmergencyStop 服务
// ═══════════════════════════════════════════════════════════
#pragma once

#include <chrono>
#include <memory>
#include <string>

#include <geometry_msgs/msg/quaternion.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <rclcpp/rclcpp.hpp>

#include "robot_common/math_utils.hpp"
#include "robot_hardware/model/types.hpp"
#include "robot_hardware/service/differential_drive.hpp"

#include <robot_msgs/srv/emergency_stop.hpp>

namespace robot_hardware::controller {

class MainNode : public rclcpp::Node {
public:
    explicit MainNode(const rclcpp::NodeOptions& options = rclcpp::NodeOptions())
        : Node("robot_hardware", options) {
        // ── 参数声明 ──
        declare_parameter<std::string>("serial_port", "/dev/ttyUSB0");
        declare_parameter<int>("baud_rate", 115200);
        declare_parameter<double>("wheel_radius", 0.05);
        declare_parameter<double>("wheel_base", 0.3);
        declare_parameter<double>("update_rate", 50.0);

        model::Config config = load_config();
        drive_service_ = std::make_unique<service::DifferentialDriveService>(config);

        // ── 发布者 ──
        odom_pub_ = create_publisher<nav_msgs::msg::Odometry>("~/output/odom", 10);

        // ── 服务 ──
        estop_srv_ = create_service<robot_msgs::srv::EmergencyStop>(
            "~/emergency_stop",
            [this](const std::shared_ptr<robot_msgs::srv::EmergencyStop::Request>,
                   std::shared_ptr<robot_msgs::srv::EmergencyStop::Response> resp) {
                drive_service_->reset();
                stopped_ = true;
                resp->success = true;
                resp->message = "已紧急停止并重置里程计";
                RCLCPP_WARN(get_logger(), "紧急停止触发");
            });

        // ── 主循环 timer ──
        const auto period = std::chrono::duration<double>(1.0 / config.update_rate);
        timer_ = create_wall_timer(std::chrono::duration_cast<std::chrono::nanoseconds>(period),
                                   [this]() { on_tick(); });

        RCLCPP_INFO(get_logger(), "硬件节点已启动 (%.1f Hz, %s)", config.update_rate,
                    config.serial_port.c_str());
    }

private:
    void on_tick() {
        if (stopped_) {
            return;
        }
        const double now_s = now().seconds();

        // TODO: 这里接真实串口读取电机速度。当前用模拟静止读数。
        model::MotorReading reading{};
        reading.left_wheel_speed = 0.0;
        reading.right_wheel_speed = 0.0;
        reading.timestamp = now_s;

        model::OdometryData odom =
            drive_service_->update_odometry(reading, 1.0 / drive_service_->config().update_rate);

        // model::OdometryData → nav_msgs::msg::Odometry
        nav_msgs::msg::Odometry odom_msg;
        odom_msg.header.stamp = now();
        odom_msg.header.frame_id = "odom";
        odom_msg.child_frame_id = "base_link";
        odom_msg.pose.pose.position.x = odom.x;
        odom_msg.pose.pose.position.y = odom.y;
        odom_msg.pose.pose.orientation = yaw_to_quaternion(odom.theta);
        odom_msg.twist.twist.linear.x = odom.linear_velocity;
        odom_msg.twist.twist.angular.z = odom.angular_velocity;
        odom_pub_->publish(odom_msg);
    }

    /// yaw (rad) → quaternion（仅绕 z 轴）。几何运算下沉到 robot_common::math，
    /// controller 只做 model↔ROS 的字段组装。
    static geometry_msgs::msg::Quaternion yaw_to_quaternion(double yaw) {
        const auto [z, w] = robot_common::math::yaw_to_quat(yaw);
        geometry_msgs::msg::Quaternion q;
        q.z = z;
        q.w = w;
        return q;
    }

    model::Config load_config() {
        model::Config c;
        c.serial_port = get_parameter("serial_port").as_string();
        c.baud_rate = get_parameter("baud_rate").as_int();
        c.wheel_radius = get_parameter("wheel_radius").as_double();
        c.wheel_base = get_parameter("wheel_base").as_double();
        c.update_rate = get_parameter("update_rate").as_double();
        return c;
    }

    std::unique_ptr<service::DifferentialDriveService> drive_service_;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
    rclcpp::Service<robot_msgs::srv::EmergencyStop>::SharedPtr estop_srv_;
    rclcpp::TimerBase::SharedPtr timer_;
    bool stopped_ = false;
};

}  // namespace robot_hardware::controller
