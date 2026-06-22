// ═══════════════════════════════════════════════════════════
//  Controller 层：ROS2 适配层
//  - 唯一知道 ROS2 存在的地方
//  - 职责：消息收发、类型转换、异常转日志
//  - 不包含业务逻辑
// ═══════════════════════════════════════════════════════════
#pragma once

#include <memory>
#include <vector>

#include <rclcpp/rclcpp.hpp>
#include <rcl_interfaces/msg/set_parameters_result.hpp>
#include <rcl_interfaces/msg/parameter.hpp>
#include <std_msgs/msg/float64.hpp>

#include "__PACKAGE_NAME__/model/types.hpp"
#include "__PACKAGE_NAME__/model/errors.hpp"
#include "__PACKAGE_NAME__/service/example_service.hpp"

namespace __PACKAGE_NAME__::controller {

class MainNode : public rclcpp::Node {
public:
    explicit MainNode(const rclcpp::NodeOptions &options = rclcpp::NodeOptions())
        : Node("__PACKAGE_NAME__", options) {
        declare_parameter("update_rate", 10.0);
        declare_parameter("threshold", 0.5);
        declare_parameter("debug", false);

        service_ = std::make_unique<service::ExampleService>(load_config());

        input_sub_ = create_subscription<std_msgs::msg::Float64>(
            "~/input/example", 10,
            [this](std_msgs::msg::Float64::SharedPtr msg) { on_input(msg); });

        output_pub_ = create_publisher<std_msgs::msg::Float64>(
            "~/output/result", 10);

        param_cb_ = add_on_set_parameters_callback(
            [this](const std::vector<rclcpp::Parameter> &p) {
                return on_param_change(p);
            });

        RCLCPP_INFO(get_logger(), "节点已启动 (rate=%.1f Hz)",
                    service_->config().update_rate);
    }

private:
    void on_input(const std_msgs::msg::Float64::SharedPtr &msg) {
        model::InputData input;
        input.value = msg->data;
        input.timestamp = now().seconds();

        try {
            auto output = service_->process(input);
            std_msgs::msg::Float64 ros_msg;
            ros_msg.data = output.result;
            output_pub_->publish(ros_msg);
        } catch (const model::InputValidationError &e) {
            RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 2000,
                                 "输入校验失败: %s", e.what());
        } catch (const model::ProcessingError &e) {
            RCLCPP_ERROR(get_logger(), "处理异常: %s", e.what());
        }
    }

    model::Config load_config() {
        model::Config c;
        c.update_rate = get_parameter("update_rate").as_double();
        c.threshold = get_parameter("threshold").as_double();
        c.debug = get_parameter("debug").as_bool();
        return c;
    }

    rcl_interfaces::msg::SetParametersResult
    on_param_change(const std::vector<rclcpp::Parameter> &) {
        service_->update_config(load_config());
        RCLCPP_INFO(get_logger(), "配置已更新 (threshold=%.3f)",
                    service_->config().threshold);
        rcl_interfaces::msg::SetParametersResult result;
        result.successful = true;
        return result;
    }

    std::unique_ptr<service::ExampleService> service_;
    rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr input_sub_;
    rclcpp::Publisher<std_msgs::msg::Float64>::SharedPtr output_pub_;
    rclcpp::Node::OnSetParametersCallbackHandle::SharedPtr param_cb_;
};

}  // namespace __PACKAGE_NAME__::controller
