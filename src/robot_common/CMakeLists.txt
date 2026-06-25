cmake_minimum_required(VERSION 3.8)
project(robot_common)

# ── 编译警告 ──
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

# ── 公共库（纯 C++，零 ROS2 依赖） ──
# pid.cpp 编译进库；math_utils.hpp 是 header-only，只随 include/ 安装。
add_library(${PROJECT_NAME} src/pid.cpp)
target_include_directories(${PROJECT_NAME} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_compile_features(${PROJECT_NAME} PUBLIC cxx_std_17)

# 导出头文件目录，使下游 find_package(robot_common) 后能直接
# #include "robot_common/math_utils.hpp"（header-only 工具传递）。
ament_export_include_directories(include)

# ── 测试 ──
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)

  ament_add_gtest(test_pid test/test_pid.cpp)
  target_link_libraries(test_pid ${PROJECT_NAME})

  ament_add_gtest(test_math_utils test/test_math_utils.cpp)
  target_link_libraries(test_math_utils ${PROJECT_NAME})
endif()

# ── 安装 ──
install(
  TARGETS ${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
)
install(
  DIRECTORY include/
  DESTINATION include
)

ament_package()
