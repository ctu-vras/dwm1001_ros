# example of launching one driver node per tag from a single launch file

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    pkg = get_package_share_directory("dwm1001_ros")
    tag_launch = os.path.join(pkg, "launch", "tag_node.launch.py")

    common_args = {
        "read_freq": "100",
        "world_frame": "world",
        "publish_tfs": "true",
    }

    return LaunchDescription(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(tag_launch),
                launch_arguments={
                    **common_args,
                    "usb_port": "/dev/ttyACM0",
                    "tag_id": "5772",
                }.items(),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(tag_launch),
                launch_arguments={
                    **common_args,
                    "usb_port": "/dev/ttyACM1",
                    "tag_id": "5773",
                }.items(),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(tag_launch),
                launch_arguments={
                    **common_args,
                    "usb_port": "/dev/ttyACM2",
                    "tag_id": "5774",
                }.items(),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(tag_launch),
                launch_arguments={
                    **common_args,
                    "usb_port": "/dev/ttyACM3",
                    "tag_id": "5775",
                }.items(),
            ),
        ]
    )
