"""测试启动：仅起 hardware + control（无感知），用于联调排错。

用法:
  ros2 launch robot_bringup test.launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    hardware_share = get_package_share_directory('robot_hardware')
    control_share = get_package_share_directory('robot_control')

    return LaunchDescription([
        Node(
            package='robot_hardware',
            executable='main_node',
            name='robot_hardware',
            output='screen',
            parameters=[os.path.join(hardware_share, 'config', 'params.yaml')],
        ),
        Node(
            package='robot_control',
            executable='main_node',
            name='robot_control',
            output='screen',
            remappings=[
                ('~/output/cmd_vel', '/cmd_vel'),
            ],
            parameters=[os.path.join(control_share, 'config', 'params.yaml')],
        ),
    ])
