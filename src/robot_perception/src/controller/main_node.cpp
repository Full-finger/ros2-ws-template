// ═══ 编译入口 ═══
#include "robot_perception/controller/main_node.hpp"

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<robot_perception::controller::MainNode>());
    rclcpp::shutdown();
    return 0;
}
