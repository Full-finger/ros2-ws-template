cmake_minimum_required(VERSION 3.8)
project(__PACKAGE_NAME__)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(action_msgs REQUIRED)

# ── 生成消息/服务/动作接口 ──
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Example.msg"
  "srv/Example.srv"
  "action/Example.action"
)

ament_export_dependencies(rosidl_default_runtime)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
