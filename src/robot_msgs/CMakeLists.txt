cmake_minimum_required(VERSION 3.8)
project(robot_msgs)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# ── 生成消息/服务/动作接口 ──
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/MotorState.msg"
  "msg/RobotStatus.msg"
  "msg/Obstacle.msg"
  "msg/ObstacleArray.msg"
  "srv/EmergencyStop.srv"
  "srv/SetMode.srv"
  "action/NavigateTo.action"
  DEPENDENCIES std_msgs geometry_msgs
)

ament_export_dependencies(rosidl_default_runtime)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
