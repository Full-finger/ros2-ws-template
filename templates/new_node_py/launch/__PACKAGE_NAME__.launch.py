"""__PACKAGE_NAME__ launch 文件。"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory('__PACKAGE_NAME__')
    return LaunchDescription([
        Node(
            package='__PACKAGE_NAME__',
            executable='main_node',
            name='__PACKAGE_NAME__',
            output='screen',
            parameters=[os.path.join(share, 'config', 'params.yaml')],
        ),
    ])
