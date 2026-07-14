# launches one node for the specified tag,
# the data from the tag is published on topic ID_[LABEL]/distances

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, Shutdown
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    prefix = LaunchConfiguration("prefix")
    usb_port = LaunchConfiguration("usb_port")
    read_freq = LaunchConfiguration("read_freq")
    world_frame = LaunchConfiguration("world_frame")
    publish_tfs = LaunchConfiguration("publish_tfs")
    tag_id = LaunchConfiguration("tag_id")

    return LaunchDescription(
        [
            DeclareLaunchArgument("prefix", default_value=""),
            DeclareLaunchArgument("usb_port", default_value="/dev/ttyACM0"),
            DeclareLaunchArgument("read_freq", default_value="10"), # 10 seems to be the max; if you change this also change fs in @follow_me/follow_me/radio_locator.py
            DeclareLaunchArgument("world_frame", default_value="world"),
            DeclareLaunchArgument("publish_tfs", default_value="true"),
            # ROS 1 tag_node.launch passed "TODO" as the pose publisher tag_id
            DeclareLaunchArgument("tag_id", default_value="TODO"),
            Node(
                package="dwm1001_ros",
                executable="uwb_tag",
                name=["uwb_tag_", tag_id],
                output="screen",
                arguments=[usb_port, read_freq, prefix],
                # mimic ROS 1 required='true': bring the launch down if the node exits
                on_exit=Shutdown(),
            ),
            Node(
                package="dwm1001_ros",
                executable="uwb_pose_publisher",
                name=["uwb_pose_publisher_", tag_id],
                output="screen",
                arguments=[world_frame, tag_id],
                condition=IfCondition(publish_tfs),
                on_exit=Shutdown(),
            ),
        ]
    )
