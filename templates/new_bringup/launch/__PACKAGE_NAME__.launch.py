"""__PACKAGE_NAME__ launch 文件。

TODO: 在这里用 IncludeLaunchDescription / Node 组装完整系统启动。
"""
from launch import LaunchDescription
from launch.actions import LogInfo


def generate_launch_description():
    return LaunchDescription([
        LogInfo(msg='TODO: 在此组装 __PACKAGE_NAME__ 的系统启动逻辑'),
    ])
