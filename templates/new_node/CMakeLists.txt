cmake_minimum_required(VERSION 3.8)
project(__PACKAGE_NAME__)

# ── 编译警告 ──
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ── 依赖 ──
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rcl_interfaces REQUIRED)
find_package(std_msgs REQUIRED)

# ── 节点可执行文件 ──
# service 层为 header-only（小型 service 约定），无需单独建库。
# 当 service 变大需要拆 .cpp 时，参考 docs/conventions.md 新建
#   add_library(${PROJECT_NAME}_service src/service/xxx.cpp)
add_executable(main_node src/main_node.cpp)
target_include_directories(main_node PRIVATE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_compile_features(main_node PRIVATE cxx_std_17)
ament_target_dependencies(main_node
  rclcpp
  rcl_interfaces
  std_msgs
)

# ── 测试（gtest，纯 Service 层，不依赖 ROS2） ──
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(test_service test/test_service.cpp)
  target_include_directories(test_service PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  )
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
