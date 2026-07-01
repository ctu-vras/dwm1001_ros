#!/usr/bin/env python3
import sys

import rclpy
from rclpy.node import Node
from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster

from geometry_msgs.msg import TransformStamped, Quaternion
from dwm1001_ros_interfaces.msg import UWBMeas, TagLocation


class UWBPose(Node):
    def __init__(self, world_frame, tag_id):
        super().__init__("uwb_pose_publisher")

        self.world = world_frame
        self.tag_id = tag_id
        self.added = []

        self.broadcaster1 = StaticTransformBroadcaster(self)
        self.broadcaster2 = TransformBroadcaster(self)

        self.subs1 = self.create_subscription(
            UWBMeas, "distances", self.add_anchors, 1
        )
        self.subs2 = self.create_subscription(
            TagLocation, "pos_estimate", self.publish_estimate, 1
        )

    def add_anchors(self, msg):
        for an in msg.measurements:
            if an.id not in self.added:
                self.get_logger().info("Adding new anchor with ID %s" % an.id)
                self.added += [an.id]
                tf = TransformStamped()
                tf.header.frame_id = self.world
                tf.header.stamp = self.get_clock().now().to_msg()
                tf.child_frame_id = "anchor_" + an.id
                tf.transform.translation.x = an.location.x
                tf.transform.translation.y = an.location.y
                tf.transform.translation.z = an.location.z
                tf.transform.rotation = Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)

                self.broadcaster1.sendTransform(tf)

    def publish_estimate(self, msg):
        tf = TransformStamped()
        tf.header.frame_id = self.world
        tf.header.stamp = self.get_clock().now().to_msg()
        tf.child_frame_id = "tag_" + self.tag_id
        tf.transform.translation.x = msg.location.x
        tf.transform.translation.y = msg.location.y
        tf.transform.translation.z = msg.location.z
        tf.transform.rotation = Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)

        self.broadcaster2.sendTransform(tf)


def main(args=None):
    rclpy.init(args=args)

    argv = rclpy.utilities.remove_ros_args(args=sys.argv)
    if len(argv) != 3:
        print("ERROR: wrong number of arguments")
        print("expected two: world_frame, tag_id")
        print("got:", argv[1:])
        rclpy.shutdown()
        return

    node = UWBPose(argv[1], argv[2])
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
