"""仿真启动：复用 full_system，强制 use_sim_time:=true。

用法:
  ros2 launch robot_bringup sim.launch.py
  （前提：已启动 Gazebo/rviz 并发布 /scan、/clock）
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    bringup_share = get_package_share_directory("robot_bringup")
    return LaunchDescription(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(bringup_share, "launch", "full_system.launch.py")
                ),
                launch_arguments={"use_sim_time": "true"}.items(),
            ),
        ]
    )
