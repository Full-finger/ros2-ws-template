"""完整系统启动：hardware + perception + control 全部节点。

用法:
  ros2 launch robot_bringup full_system.launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    hardware_share = get_package_share_directory('robot_hardware')
    perception_share = get_package_share_directory('robot_perception_py')
    control_share = get_package_share_directory('robot_control')

    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='是否使用仿真时钟'),

        # ── 硬件层 ──
        Node(
            package='robot_hardware',
            executable='main_node',
            name='robot_hardware',
            output='screen',
            parameters=[
                os.path.join(hardware_share, 'config', 'params.yaml'),
                {'use_sim_time': use_sim_time},
            ],
        ),

        # ── 感知层 ──
        Node(
            package='robot_perception_py',
            executable='main_node',
            name='robot_perception',
            output='screen',
            remappings=[('~/input/scan', '/scan')],
            parameters=[
                os.path.join(perception_share, 'config', 'params.yaml'),
                {'use_sim_time': use_sim_time},
            ],
        ),

        # ── 控制层 ──
        Node(
            package='robot_control',
            executable='main_node',
            name='robot_control',
            output='screen',
            remappings=[
                ('~/input/obstacles', '/robot_perception/output/obstacles'),
                ('~/output/cmd_vel', '/cmd_vel'),
            ],
            parameters=[
                os.path.join(control_share, 'config', 'params.yaml'),
                {'use_sim_time': use_sim_time},
            ],
        ),
    ])
