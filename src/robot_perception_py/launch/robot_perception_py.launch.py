"""robot_perception_py launch 文件。"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory('robot_perception_py')
    return LaunchDescription([
        Node(
            package='robot_perception_py',
            executable='main_node',
            name='robot_perception',
            output='screen',
            parameters=[os.path.join(share, 'config', 'params.yaml')],
        ),
    ])
