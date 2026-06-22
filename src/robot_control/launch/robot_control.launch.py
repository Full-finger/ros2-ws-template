"""robot_control launch 文件。"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='robot_control',
            executable='main_node',
            name='robot_control',
            output='screen',
            parameters=['config/params.yaml'],
        ),
    ])
