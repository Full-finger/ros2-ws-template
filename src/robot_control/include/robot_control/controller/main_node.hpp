// ═══════════════════════════════════════════════════════════
//  Controller 层：ROS2 适配
//  - 订阅障碍物（robot_msgs/ObstacleArray）→ model::Threat
//  - 收到障碍物时调 SafetyVelocityService，发布 geometry_msgs/Twist
// ═══════════════════════════════════════════════════════════
#pragma once

#include <memory>
#include <vector>

#include <geometry_msgs/msg/twist.hpp>
#include <rclcpp/rclcpp.hpp>

#include "robot_control/model/types.hpp"
#include "robot_control/service/safety_velocity.hpp"

#include <robot_msgs/msg/obstacle_array.hpp>

namespace robot_control::controller {

class MainNode : public rclcpp::Node {
public:
    explicit MainNode(const rclcpp::NodeOptions& options = rclcpp::NodeOptions())
        : Node("robot_control", options) {
        declare_parameter<double>("target_linear_speed", 0.5);
        declare_parameter<double>("max_angular_speed", 1.5);
        declare_parameter<double>("safe_distance", 0.8);

        safety_service_ = std::make_unique<service::SafetyVelocityService>(load_config());

        obstacles_sub_ = create_subscription<robot_msgs::msg::ObstacleArray>(
            "~/input/obstacles", 10,
            [this](robot_msgs::msg::ObstacleArray::SharedPtr msg) { on_obstacles(msg); });

        cmd_pub_ = create_publisher<geometry_msgs::msg::Twist>("~/output/cmd_vel", 10);

        last_tick_ = now();
        RCLCPP_INFO(get_logger(), "控制节点已启动 (safe_dist=%.2f m)",
                    safety_service_->config().safe_distance);
    }

private:
    void on_obstacles(const robot_msgs::msg::ObstacleArray::SharedPtr& msg) {
        const rclcpp::Time t = now();
        const double dt = (t - last_tick_).seconds();
        last_tick_ = t;
        if (dt <= 0.0)
            return;  // 首帧或时钟异常，跳过

        // robot_msgs/ObstacleArray → model::Threat
        std::vector<model::Threat> threats;
        threats.reserve(msg->obstacles.size());
        for (const auto& ob : msg->obstacles) {
            model::Threat th;
            th.distance = std::hypot(ob.center.x, ob.center.y);
            th.bearing = std::atan2(ob.center.y, ob.center.x);
            threats.push_back(th);
        }

        model::TwistCmd cmd = safety_service_->compute(threats, dt);

        // model::TwistCmd → geometry_msgs/Twist
        geometry_msgs::msg::Twist twist;
        twist.linear.x = cmd.linear;
        twist.angular.z = cmd.angular;
        cmd_pub_->publish(twist);
    }

    model::Config load_config() {
        model::Config c;
        c.target_linear_speed = get_parameter("target_linear_speed").as_double();
        c.max_angular_speed = get_parameter("max_angular_speed").as_double();
        c.safe_distance = get_parameter("safe_distance").as_double();
        return c;
    }

    std::unique_ptr<service::SafetyVelocityService> safety_service_;
    rclcpp::Subscription<robot_msgs::msg::ObstacleArray>::SharedPtr obstacles_sub_;
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_pub_;
    rclcpp::Time last_tick_;
};

}  // namespace robot_control::controller
