#!/usr/bin/env python3
# Copyright 2024 ROS2 Tutorial Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# INSTRUCTOR NOTES — TWO PLANTED BUGS (do not share with students)
#
# Bug 1 (topic name): on_configure subscribes to '/wrong_turtle/goal'
#   instead of 'goal'. The absolute path does not resolve to the publisher's
#   topic (/turtle1/goal). Visible in rqt_graph as a missing connection
#   between goal_point_publisher and the controller; also visible via
#   ros2 node info /turtle_lf_controller_broken (shows /wrong_turtle/goal).
#   Fix: change '/wrong_turtle/goal' to 'goal'.
#
# Bug 2 (QoS mismatch): on_configure creates the pose subscription with
#   ReliabilityPolicy.RELIABLE. turtlesim publishes Pose with BEST_EFFORT.
#   RELIABLE subscriber + BEST_EFFORT publisher = 0 matched publishers.
#   Visible via: ros2 topic info --verbose /turtle1/pose (Matched Publishers: 0).
#   Fix: use QoSPresetProfiles.SENSOR_DATA.value.

from typing import Optional

import rclpy
from rclpy.lifecycle import LifecycleNode
from rclpy.lifecycle import TransitionCallbackReturn
from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy
from rcl_interfaces.msg import SetParametersResult

from geometry_msgs.msg import Point
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from turtlesim_controller.control_law import compute_go_to_goal_control


class TurtleLFControllerBroken(LifecycleNode):

    def __init__(self):
        super().__init__('turtle_lf_controller_broken')

        self.declare_parameter('kv', 1.0)
        self.declare_parameter('kw', 5.0)
        self.declare_parameter('tolerance', 0.01)
        self.declare_parameter('control_loop_frequency', 10.0)

        self.kv = 1.0
        self.kw = 5.0
        self.tolerance = 0.01
        self.control_loop_frequency = 10.0
        self.control_period = 1.0 / self.control_loop_frequency

        self.current_pose: Optional[list] = None
        self.current_goal: Optional[list] = None

        self.pose_sub = None
        self.goal_sub = None
        self.cmd_vel_pub = None
        self.control_timer = None

        self.controller_enabled = False

        self.add_on_set_parameters_callback(self.parameter_update_callback)

        self.get_logger().info('BrokenController constructed. State: unconfigured.')

    # -------------------------------------------------------------------------
    # Lifecycle callbacks
    # -------------------------------------------------------------------------

    def on_configure(self, state):
        self.get_logger().info('Configuring BrokenController...')

        try:
            self.kv = float(self.get_parameter('kv').value)
            self.kw = float(self.get_parameter('kw').value)
            self.tolerance = float(self.get_parameter('tolerance').value)
            self.control_loop_frequency = float(
                self.get_parameter('control_loop_frequency').value
            )
            self.control_period = 1.0 / self.control_loop_frequency

            # BUG 1: Wrong topic name — should be 'goal', not '/wrong_turtle/goal'
            self.goal_sub = self.create_subscription(
                Point,
                '/wrong_turtle/goal',
                self.goal_callback,
                10
            )

            # BUG 2: Wrong QoS — should be QoSPresetProfiles.SENSOR_DATA.value
            broken_qos = QoSProfile(
                depth=10,
                reliability=ReliabilityPolicy.RELIABLE,
            )
            self.pose_sub = self.create_subscription(
                Pose,
                'pose',
                self.pose_callback,
                broken_qos
            )

            self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)

            self.control_timer = self.create_timer(
                self.control_period, self.control_loop
            )

            self.controller_enabled = False
            self.current_pose = None
            self.current_goal = None

            self.get_logger().info('Configuration complete.')
            return TransitionCallbackReturn.SUCCESS

        except Exception as exc:
            self.get_logger().error(f'Exception during configure: {exc}')
            return TransitionCallbackReturn.FAILURE

    def on_activate(self, state):
        self.get_logger().info('Activating BrokenController...')
        self.controller_enabled = True
        return TransitionCallbackReturn.SUCCESS

    def on_deactivate(self, state):
        self.get_logger().info('Deactivating BrokenController...')
        self.controller_enabled = False
        self.publish_zero_twist()
        return TransitionCallbackReturn.SUCCESS

    def on_cleanup(self, state):
        self.controller_enabled = False
        self.publish_zero_twist()
        if self.control_timer is not None:
            self.destroy_timer(self.control_timer)
            self.control_timer = None
        if self.pose_sub is not None:
            self.destroy_subscription(self.pose_sub)
            self.pose_sub = None
        if self.goal_sub is not None:
            self.destroy_subscription(self.goal_sub)
            self.goal_sub = None
        if self.cmd_vel_pub is not None:
            self.destroy_publisher(self.cmd_vel_pub)
            self.cmd_vel_pub = None
        self.current_pose = None
        self.current_goal = None
        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state):
        self.controller_enabled = False
        self.publish_zero_twist()
        return TransitionCallbackReturn.SUCCESS

    def on_error(self, state):
        self.controller_enabled = False
        self.publish_zero_twist()
        return TransitionCallbackReturn.SUCCESS

    # -------------------------------------------------------------------------
    # Parameter handling
    # -------------------------------------------------------------------------

    def parameter_update_callback(self, parameters):
        new_kv = self.kv
        new_kw = self.kw
        new_tolerance = self.tolerance
        new_freq = self.control_loop_frequency

        for param in parameters:
            if param.name == 'kv':
                new_kv = float(param.value)
            elif param.name == 'kw':
                new_kw = float(param.value)
            elif param.name == 'tolerance':
                new_tolerance = float(param.value)
            elif param.name == 'control_loop_frequency':
                new_freq = float(param.value)

        if new_kv < 0 or new_kw < 0 or new_tolerance <= 0 or new_freq <= 0:
            return SetParametersResult(successful=False, reason='Invalid parameter value.')

        self.kv = new_kv
        self.kw = new_kw
        self.tolerance = new_tolerance
        self.control_loop_frequency = new_freq
        self.control_period = 1.0 / self.control_loop_frequency

        return SetParametersResult(successful=True)

    # -------------------------------------------------------------------------
    # ROS callbacks
    # -------------------------------------------------------------------------

    def pose_callback(self, msg: Pose):
        self.current_pose = [msg.x, msg.y, msg.theta]

    def goal_callback(self, msg: Point):
        self.current_goal = [msg.x, msg.y]
        self.get_logger().info(f'Goal received: x={msg.x:.3f}, y={msg.y:.3f}')

    def control_loop(self):
        if not self.controller_enabled:
            return
        if self.current_pose is None:
            self.publish_zero_twist()
            return
        if self.current_goal is None:
            self.publish_zero_twist()
            return

        v, w, d = compute_go_to_goal_control(
            pose=self.current_pose,
            goal=self.current_goal,
            Kv=self.kv,
            Kw=self.kw,
            tolerance=self.tolerance,
        )

        if d < self.tolerance:
            self.publish_zero_twist()
            return

        cmd = Twist()
        cmd.linear.x = v
        cmd.angular.z = w
        self.cmd_vel_pub.publish(cmd)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def publish_zero_twist(self):
        if self.cmd_vel_pub is None:
            return
        self.cmd_vel_pub.publish(Twist())


def main(args=None):
    rclpy.init(args=args)
    node = TurtleLFControllerBroken()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard interrupt.')
    finally:
        node.publish_zero_twist()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
