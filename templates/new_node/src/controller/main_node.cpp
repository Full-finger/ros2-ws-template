// ═══ 编译入口 ═══
#include "__PACKAGE_NAME__/controller/main_node.hpp"

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<__PACKAGE_NAME__::controller::MainNode>());
    rclcpp::shutdown();
    return 0;
}
