// ═══════════════════════════════════════════════════════════
//  Controller 层：ROS2 适配
//  - 订阅 LaserScan
//  - 调 GridClusterService 聚类
//  - model 障碍物 → robot_msgs/ObstacleArray 发布
// ═══════════════════════════════════════════════════════════
#pragma once

#include <memory>
#include <vector>

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/laser_scan.hpp>

#include <robot_msgs/msg/obstacle.hpp>
#include <robot_msgs/msg/obstacle_array.hpp>

#include "robot_perception/model/types.hpp"
#include "robot_perception/service/grid_cluster.hpp"

namespace robot_perception::controller {

class MainNode : public rclcpp::Node {
public:
    explicit MainNode(const rclcpp::NodeOptions &options = rclcpp::NodeOptions())
        : Node("robot_perception", options) {
        declare_parameter<double>("max_range", 5.0);
        declare_parameter<double>("min_range", 0.05);
        declare_parameter<double>("cell_size", 0.2);
        declare_parameter<int>("min_points", 1);

        cluster_service_ =
            std::make_unique<service::GridClusterService>(load_config());

        scan_sub_ = create_subscription<sensor_msgs::msg::LaserScan>(
            "~/input/scan", 10,
            [this](sensor_msgs::msg::LaserScan::SharedPtr msg) { on_scan(msg); });

        obstacles_pub_ =
            create_publisher<robot_msgs::msg::ObstacleArray>("~/output/obstacles", 10);

        RCLCPP_INFO(get_logger(), "感知节点已启动 (cell=%.2f m)",
                    cluster_service_->config().cell_size);
    }

private:
    void on_scan(const sensor_msgs::msg::LaserScan::SharedPtr &msg) {
        // ROS LaserScan → model::LaserPoint
        std::vector<model::LaserPoint> points;
        points.reserve(msg->ranges.size());
        for (size_t i = 0; i < msg->ranges.size(); ++i) {
            model::LaserPoint p;
            p.range = msg->ranges[i];
            p.angle = msg->angle_min + msg->angle_increment * i;
            points.push_back(p);
        }

        // 聚类
        auto protos = cluster_service_->cluster(points);

        // model::ObstacleProto → robot_msgs/ObstacleArray
        robot_msgs::msg::ObstacleArray out;
        out.header = msg->header;
        out.obstacles.reserve(protos.size());
        for (const auto &pr : protos) {
            robot_msgs::msg::Obstacle ob;
            ob.center.x = pr.x;
            ob.center.y = pr.y;
            ob.center.z = 0.0;
            ob.radius = pr.radius;
            ob.confidence = static_cast<uint8_t>(
                std::min(100, pr.count * 10));  // 点数 → 置信度
            out.obstacles.push_back(ob);
        }
        obstacles_pub_->publish(out);

        RCLCPP_DEBUG(get_logger(), "聚类出 %zu 个障碍物", protos.size());
    }

    model::Config load_config() {
        model::Config c;
        c.max_range = get_parameter("max_range").as_double();
        c.min_range = get_parameter("min_range").as_double();
        c.cell_size = get_parameter("cell_size").as_double();
        c.min_points = get_parameter("min_points").as_int();
        return c;
    }

    std::unique_ptr<service::GridClusterService> cluster_service_;
    rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr scan_sub_;
    rclcpp::Publisher<robot_msgs::msg::ObstacleArray>::SharedPtr obstacles_pub_;
};

}  // namespace robot_perception::controller
