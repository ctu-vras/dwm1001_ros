#!/usr/bin/env python3
import sys
import time
import serial

import rclpy
from rclpy.node import Node

from dwm1001_ros_interfaces.msg import UWBMeas, Anchor, TagLocation
from std_msgs.msg import String


class UWBTag(Node):
    def __init__(self, usb_port, freq, prefix):
        super().__init__("uwb_tag")

        self.sound_pub = self.create_publisher(String, "/log_sound", 1)
        time.sleep(1.0)

        self.usb = usb_port
        self.frequency = freq
        self.prefix = prefix

        self.ser = None
        self.tim = None
        self.tim2 = None
        self.received = 0
        self.failures = 0

        # open the port and start publishing
        self.serial_setup()
        time.sleep(0.5)
        if self.ser is not None:
            id = self.set_uwb_mode()

            prefix = "ID_" + id + "/"

            self.pub1 = self.create_publisher(UWBMeas, self.prefix + prefix + "distances", 1)
            self.pub2 = self.create_publisher(TagLocation, self.prefix + prefix + "pos_estimate", 1)

            self.tim = self.create_timer(1 / self.frequency, self.read_data)
        else:
            self.get_logger().fatal("Serial port can not be opened, quitting")
            self.log_sound("T W R: Serial port can not be opened, quitting")
            raise RuntimeError("Cannot open serial port")

        self.tim2 = self.create_timer(3.0, self.test_connection)

    def log_sound(self, text):
        self.sound_pub.publish(String(data=text))

    def shutdown(self):
        if self.tim2 is not None:
            self.tim2.cancel()
        if self.tim is not None:
            self.tim.cancel()
        if self.ser is not None:
            self.close_serial()
            self.ser.close()
        self.get_logger().info("Shutting down")

    def test_connection(self):
        if self.received == 0:
            self.get_logger().warn("No data received in the last 3 seconds")
            self.log_sound("T W R: No data received in the last 3 seconds")
            self.failures += 1
        else:
            self.received = 0
            self.failures = 0
        if self.failures == 3:
            self.get_logger().fatal("No data received in the last 9 seconds, quitting")
            self.log_sound("T W R: No data received in the last 9 seconds, quitting")
            raise SystemExit("no data")

    def serial_setup(self):
        try:
            self.ser = serial.Serial(self.usb, 115200, timeout=0.1)
            if self.ser.is_open:
                self.get_logger().info("Serial comm started at : %s" % self.usb)
            else:
                self.get_logger().fatal("Can't open %s" % self.usb)
                self.log_sound("T W R: can't open serial port")
                self.ser = None
        except serial.SerialException:
            self.get_logger().fatal("Can't open %s" % self.usb)
            self.log_sound("T W R: can't open serial port")
            self.ser = None

    def close_serial(self):
        self.get_logger().info("Closing connection")
        try:
            self.ser.write(b"les\r")
        except serial.SerialException as ex:
            self.get_logger().fatal("Serial exception [%s]" % ex)
        time.sleep(0.1)
        self.get_logger().info("Connection to tag closed")

    def set_uwb_mode(self):
        self.get_logger().info("Setting UWB tag")
        self.ser.write(b"\r")
        time.sleep(0.5)
        self.ser.write(b"\r")
        time.sleep(0.5)
        # obtain the ID
        self.ser.write(b"si\r")
        time.sleep(0.5)
        id = ""
        while rclpy.ok():
            d = self.read_serial()
            if d is None:
                self.get_logger().error("Communication compromised, trying to reset the port")
                self.serial_setup()
            elif len(d) > 3 and d[2].decode("utf-8")[0:3] == "cfg":
                # the line with the module label, label is the last field (e.g. label=DW5722)
                id = d[-1].decode("utf-8")[-4:]
                self.get_logger().info("The tag has ID %s" % id)
                id_mod = ""
                for i in range(len(id) - 1):
                    id_mod += id[i] + " "
                id_mod += id[-1]
                self.log_sound("T W R: connected to tag %s" % id_mod)
                break
            time.sleep(0.01)
        if len(id) == 0:
            self.get_logger().error("ID retrieval failed")
            self.log_sound("T W R: cannot retrieve the ID of the module")
            raise RuntimeError("Cannot retrieve the module ID")
        time.sleep(0.1)
        self.ser.write(b"les\r")
        time.sleep(0.3)
        self.get_logger().info("Setup done")
        return id

    def read_serial(self, shutdown=True):
        if self.ser.is_open:
            try:
                raw_data = self.ser.readline()
            except serial.SerialException as ex:
                self.get_logger().fatal("Serial exception [%s]" % ex)
                self.log_sound("T W R: serial exception")
                if shutdown:
                    raise SystemExit("Connection failed")
                else:
                    return None
            data = raw_data.split()
            return data
        else:
            return None

    def reconnect(self):
        # connection lost try to open the port again
        self.get_logger().info("Trying to reconnect to UWB module")
        if self.tim is not None:
            self.tim.cancel()
        if self.tim2 is not None:
            self.tim2.cancel()
        k = 0
        while k < 3:
            time.sleep(2)
            try:
                self.ser = serial.Serial(self.usb, 115200, timeout=0.1)
                if self.ser.is_open:
                    self.get_logger().info("Reconnected to: %s" % self.usb)
                    self.set_uwb_mode()
                    self.tim = self.create_timer(1 / self.frequency, self.read_data)
                    self.tim2 = self.create_timer(3.0, self.test_connection)
                    return
                else:
                    self.get_logger().error(
                        "Attempt %d failed, will try again in 2 seconds" % (k + 1)
                    )
            except serial.SerialException:
                self.get_logger().error(
                    "Attempt %d failed, will try again in 2 seconds" % (k + 1)
                )
            k += 1
        self.get_logger().fatal("Cannot restore the connection")
        raise SystemExit("cannot connect to serial port")

    def read_data(self):
        data = self.read_serial(False)  # list of bytes
        if data is None:
            self.reconnect()
        else:
            self.received += 1
            meas = UWBMeas()
            est = TagLocation()
            est_received = False
            no_warn = False
            for m in data:
                m_str = m.decode("utf-8")
                if len(m_str) >= 25 and m_str[4] == "[":
                    # distance from one of the anchors
                    # e.q. 1151[5.00,8.00,2.25]=6.48
                    a = Anchor()
                    a.id = m_str[0:4]  # 1151

                    p = m_str[5:19].split(",")  # list, ['5.00', '8.00', '2.25']
                    a.location.x = float(p[0])
                    a.location.y = float(p[1])
                    a.location.z = float(p[2])

                    a.dist = float(m_str[21:])  # 6.48
                    meas.measurements += [a]
                elif m_str[0:5] == "le_us":
                    # computation time
                    # e.g. le_us=2576
                    est.computation_time = int(m_str[6:10])  # 2576
                    est_received = True
                elif m_str[0:3] == "est":
                    # estimated position
                    # e.g. est[2.57,1.98,1.68,100]
                    d = m_str[4:23].split(",")  # list, ['2.57', '1.98', '1.68', '100']
                    est.location.x = float(d[0])
                    est.location.y = float(d[1])
                    est.location.z = float(d[2])
                    est.quality = int(d[3])
                elif m_str[0:3] == "dwm":
                    no_warn = True
                    break
                elif m_str in ["DWM1001", "Copyright", "License", "Compiled", "Help"]:
                    # welcome message
                    no_warn = True
                    if m_str == "DWM1001":
                        self.get_logger().info("Welcome message from the tag:")
                    s = ""
                    for i in range(len(data) - 1):
                        s += data[i].decode("utf-8") + " "
                    s += data[-1].decode("utf-8")
                    self.get_logger().info(s)
                    break
                elif b"INF]" in data:
                    no_warn = True
                    break
                else:
                    self.get_logger().error("Unknown message from the tag [%s]" % (data))
                    break
            if len(data) == 0 and not no_warn:
                self.get_logger().warn("Empty message received")
            elif len(meas.measurements) == 0 and not no_warn:
                self.get_logger().warn("Message with no range data, received:[%s]" % str(data))
            self.pub1.publish(meas)
            if est_received:
                self.pub2.publish(est)


def main(args=None):
    rclpy.init(args=args)

    argv = rclpy.utilities.remove_ros_args(args=sys.argv)
    if len(argv) != 4:
        print("ERROR: wrong number of arguments")
        print("expected three: usb_port, read_frequency, prefix")
        print("got:", argv[1:])
        rclpy.shutdown()
        return

    node = UWBTag(argv[1], float(argv[2]), argv[3])
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
