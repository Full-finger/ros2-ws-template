"""__PACKAGE_NAME__ launch 文件。"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='__PACKAGE_NAME__',
            executable='main_node',
            name='__PACKAGE_NAME__',
            output='screen',
            parameters=['config/params.yaml'],
        ),
    ])
