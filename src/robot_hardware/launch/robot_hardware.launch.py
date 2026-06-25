"""robot_hardware launch 文件。"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory("robot_hardware")
    return LaunchDescription(
        [
            Node(
                package="robot_hardware",
                executable="main_node",
                name="robot_hardware",
                output="screen",
                parameters=[os.path.join(share, "config", "params.yaml")],
            ),
        ]
    )
