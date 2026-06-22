cmake_minimum_required(VERSION 3.8)
project(__PACKAGE_NAME__)

find_package(ament_cmake REQUIRED)

# bringup 包不编译任何代码，只安装 launch 和 config
install(
  DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
