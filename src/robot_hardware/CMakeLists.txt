cmake_minimum_required(VERSION 3.8)
project(robot_hardware)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(robot_common REQUIRED)
find_package(robot_msgs REQUIRED)

# ── 节点可执行文件 ──
add_executable(main_node src/controller/main_node.cpp)
target_include_directories(main_node PRIVATE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_compile_features(main_node PRIVATE cxx_std_17)
ament_target_dependencies(main_node
  rclcpp
  nav_msgs
  sensor_msgs
  geometry_msgs
  robot_common
  robot_msgs
)

# ── 测试（纯运动学逻辑，不依赖 ROS2 运行时） ──
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(test_differential_drive test/test_differential_drive.cpp)
  target_include_directories(test_differential_drive PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  )
  # service 层 include 了 robot_common 的 header-only 工具
  ament_target_dependencies(test_differential_drive robot_common)
endif()

# ── 安装 ──
install(
  TARGETS main_node
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)
install(
  DIRECTORY include/
  DESTINATION include
)
install(
  DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
