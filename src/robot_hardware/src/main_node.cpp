// ═══ 编译入口 ═══
#include "robot_hardware/controller/main_node.hpp"

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<robot_hardware::controller::MainNode>());
    rclcpp::shutdown();
    return 0;
}
