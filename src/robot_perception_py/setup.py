from setuptools import find_packages, setup

PACKAGE_NAME = "robot_perception_py"

setup(
    name=PACKAGE_NAME,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + PACKAGE_NAME]),
        ("share/" + PACKAGE_NAME, ["package.xml"]),
        ("share/" + PACKAGE_NAME + "/launch", ["launch/robot_perception_py.launch.py"]),
        ("share/" + PACKAGE_NAME + "/config", ["config/params.yaml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="robot team",
    maintainer_email="dev@robot.lab",
    description="感知：激光点质心提取，输出障碍物列表（Python 实现）",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            # ROS2 executable = 模块路径:main 函数
            # controller 层是唯一接触 rclpy 的入口
            "main_node = robot_perception_py.controller.main_node:main",
        ],
    },
)
