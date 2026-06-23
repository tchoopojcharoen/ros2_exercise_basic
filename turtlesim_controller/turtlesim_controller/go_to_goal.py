#!/usr/bin/env python3

from typing import Optional

import rclpy
from rclpy.lifecycle import LifecycleNode
from rclpy.lifecycle import TransitionCallbackReturn
from rcl_interfaces.msg import SetParametersResult

from geometry_msgs.msg import Point
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from turtlesim_controller.control_law import compute_go_to_goal_control


class GoToGoalController(LifecycleNode):
    """
    Lifecycle go-to-goal controller for turtlesim.

    Topics
    ------
    Subscribes:
        pose : turtlesim/msg/Pose
        goal : geometry_msgs/msg/Point

    Publishes:
        cmd_vel : geometry_msgs/msg/Twist

    Parameters
    ----------
    kv : float
        Linear velocity gain. Default: 1.0

    kw : float
        Angular velocity gain. Default: 5.0

    tolerance : float
        Goal distance tolerance. Default: 0.01

    control_loop_frequency : float
        Control loop frequency in Hz. Default: 10.0

        This parameter can be changed dynamically. When updated,
        the controller recreates its timer with the new period.
    """

    def __init__(self):
        super().__init__('go_to_goal_controller')

        # Declare parameters.
        self.declare_parameter('kv', 1.0)
        self.declare_parameter('kw', 5.0)
        self.declare_parameter('tolerance', 0.01)
        self.declare_parameter('control_loop_frequency', 10.0)

        # Runtime parameter values.
        self.kv = 1.0
        self.kw = 5.0
        self.tolerance = 0.01
        self.control_loop_frequency = 10.0
        self.control_period = 1.0 / self.control_loop_frequency

        # Latest received data.
        self.current_pose: Optional[list[float]] = None
        self.current_goal: Optional[list[float]] = None

        # ROS entities. They are created during configure().
        self.pose_sub = None
        self.goal_sub = None
        self.cmd_vel_pub = None
        self.control_timer = None

        # Internal active flag.
        self.controller_enabled = False

        # Dynamic parameter callback.
        self.add_on_set_parameters_callback(self.parameter_update_callback)

        self.get_logger().info(
            'Lifecycle node constructed. Current state: unconfigured.'
        )

    # -------------------------------------------------------------------------
    # Lifecycle callbacks
    # -------------------------------------------------------------------------

    def on_configure(self, state):
        """
        Configure the controller.

        This is where we:
        - read parameters
        - validate parameters
        - create subscribers
        - create publisher
        - create timer
        """

        self.get_logger().info('Configuring go_to_goal_controller...')

        try:
            self.kv = float(self.get_parameter('kv').value)
            self.kw = float(self.get_parameter('kw').value)
            self.tolerance = float(self.get_parameter('tolerance').value)
            self.control_loop_frequency = float(
                self.get_parameter('control_loop_frequency').value
            )

            validation_result = self.validate_controller_parameters(
                kv=self.kv,
                kw=self.kw,
                tolerance=self.tolerance,
                control_loop_frequency=self.control_loop_frequency
            )

            if not validation_result.successful:
                self.get_logger().error(validation_result.reason)
                return TransitionCallbackReturn.FAILURE

            self.control_period = 1.0 / self.control_loop_frequency

            self.pose_sub = self.create_subscription(
                Pose,
                'pose',
                self.pose_callback,
                10
            )

            self.goal_sub = self.create_subscription(
                Point,
                'goal',
                self.goal_callback,
                10
            )

            self.cmd_vel_pub = self.create_publisher(
                Twist,
                'cmd_vel',
                10
            )

            self.create_control_timer()

            self.controller_enabled = False
            self.current_pose = None
            self.current_goal = None

            self.get_logger().info(
                'Configured with '
                f'kv={self.kv}, '
                f'kw={self.kw}, '
                f'tolerance={self.tolerance}, '
                f'control_loop_frequency={self.control_loop_frequency} Hz, '
                f'control_period={self.control_period:.6f} s'
            )

            return TransitionCallbackReturn.SUCCESS

        except Exception as exc:
            self.get_logger().error(f'Exception during configure: {exc}')
            return TransitionCallbackReturn.FAILURE

    def on_activate(self, state):
        """
        Activate the controller.

        After this transition, the control loop is allowed to publish cmd_vel.
        """

        self.get_logger().info('Activating go_to_goal_controller...')

        self.controller_enabled = True

        self.get_logger().info(
            'Controller is now active. Waiting for pose and goal...'
        )

        return TransitionCallbackReturn.SUCCESS

    def on_deactivate(self, state):
        """
        Deactivate the controller.

        Stop active control and publish zero velocity.
        """

        self.get_logger().info('Deactivating go_to_goal_controller...')

        self.controller_enabled = False
        self.publish_zero_twist()

        self.get_logger().info('Controller deactivated. Published zero Twist.')

        return TransitionCallbackReturn.SUCCESS

    def on_cleanup(self, state):
        """
        Cleanup the controller.

        Destroy ROS entities and return to unconfigured.
        """

        self.get_logger().info('Cleaning up go_to_goal_controller...')

        self.controller_enabled = False

        # Try to stop the turtle before destroying the publisher.
        self.publish_zero_twist()

        self.destroy_control_timer()

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

        self.get_logger().info('Cleanup complete.')

        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state):
        """
        Shutdown the controller.

        Always try to stop the turtle before shutdown.
        """

        self.get_logger().info('Shutting down go_to_goal_controller...')

        self.controller_enabled = False
        self.publish_zero_twist()

        return TransitionCallbackReturn.SUCCESS

    def on_error(self, state):
        """
        Error handling transition.

        In an error case, command zero velocity.
        """

        self.get_logger().error('Lifecycle error occurred. Publishing zero Twist.')

        self.controller_enabled = False
        self.publish_zero_twist()

        return TransitionCallbackReturn.SUCCESS

    # -------------------------------------------------------------------------
    # Dynamic parameter handling
    # -------------------------------------------------------------------------

    def parameter_update_callback(self, parameters):
        """
        Dynamically handle parameter updates.

        Supported dynamic parameters:
        - kv
        - kw
        - tolerance
        - control_loop_frequency

        Updating control_loop_frequency recreates the timer with the new period.
        """

        new_kv = self.kv
        new_kw = self.kw
        new_tolerance = self.tolerance
        new_control_loop_frequency = self.control_loop_frequency

        for param in parameters:
            if param.name == 'kv':
                new_kv = float(param.value)

            elif param.name == 'kw':
                new_kw = float(param.value)

            elif param.name == 'tolerance':
                new_tolerance = float(param.value)

            elif param.name == 'control_loop_frequency':
                new_control_loop_frequency = float(param.value)

        validation_result = self.validate_controller_parameters(
            kv=new_kv,
            kw=new_kw,
            tolerance=new_tolerance,
            control_loop_frequency=new_control_loop_frequency
        )

        if not validation_result.successful:
            return validation_result

        frequency_changed = (
            abs(new_control_loop_frequency - self.control_loop_frequency) > 1e-12
        )

        self.kv = new_kv
        self.kw = new_kw
        self.tolerance = new_tolerance

        if frequency_changed:
            self.control_loop_frequency = new_control_loop_frequency
            self.control_period = 1.0 / self.control_loop_frequency

            # If the node has already been configured, the timer exists and can
            # be recreated immediately. If not configured yet, only update the
            # stored value; the timer will be created during on_configure().
            if self.control_timer is not None:
                self.recreate_control_timer()

            self.get_logger().info(
                f'Updated control_loop_frequency to '
                f'{self.control_loop_frequency:.3f} Hz '
                f'({self.control_period:.6f} s period)'
            )

        self.get_logger().info(
            'Updated parameters: '
            f'kv={self.kv}, '
            f'kw={self.kw}, '
            f'tolerance={self.tolerance}, '
            f'control_loop_frequency={self.control_loop_frequency}'
        )

        return SetParametersResult(successful=True)

    def validate_controller_parameters(
        self,
        kv,
        kw,
        tolerance,
        control_loop_frequency
    ):
        """
        Validate controller parameters.

        Returns
        -------
        SetParametersResult
            successful=True if valid.
            successful=False with reason if invalid.
        """

        if kv < 0.0:
            return SetParametersResult(
                successful=False,
                reason='Parameter kv must be non-negative.'
            )

        if kw < 0.0:
            return SetParametersResult(
                successful=False,
                reason='Parameter kw must be non-negative.'
            )

        if tolerance <= 0.0:
            return SetParametersResult(
                successful=False,
                reason='Parameter tolerance must be positive.'
            )

        if control_loop_frequency <= 0.0:
            return SetParametersResult(
                successful=False,
                reason='Parameter control_loop_frequency must be positive.'
            )

        return SetParametersResult(successful=True)

    # -------------------------------------------------------------------------
    # ROS callbacks
    # -------------------------------------------------------------------------

    def pose_callback(self, msg: Pose):
        """
        Store latest turtlesim pose.
        """

        self.current_pose = [
            msg.x,
            msg.y,
            msg.theta
        ]

    def goal_callback(self, msg: Point):
        """
        Store latest goal point.

        z is ignored for turtlesim.
        """

        self.current_goal = [
            msg.x,
            msg.y
        ]

        self.get_logger().info(
            f'Received new goal: x={msg.x:.3f}, y={msg.y:.3f}'
        )

    def control_loop(self):
        """
        Periodic controller loop.

        The timer exists after configure(), but it only publishes control
        commands when the lifecycle node is active.
        """

        if not self.controller_enabled:
            return

        if self.current_pose is None:
            self.get_logger().debug('No pose received yet. Publishing zero Twist.')
            self.publish_zero_twist()
            return

        if self.current_goal is None:
            self.get_logger().debug('No goal received yet. Publishing zero Twist.')
            self.publish_zero_twist()
            return

        v, w, d = compute_go_to_goal_control(
            pose=self.current_pose,
            goal=self.current_goal,
            Kv=self.kv,
            Kw=self.kw,
            tolerance=self.tolerance
        )

        if d < self.tolerance:
            self.publish_zero_twist()
            self.get_logger().debug(
                f'Goal reached. d={d:.4f} < tolerance={self.tolerance:.4f}'
            )
            return

        cmd = Twist()
        cmd.linear.x = v
        cmd.angular.z = w

        self.cmd_vel_pub.publish(cmd)

        self.get_logger().debug(
            f'Publishing cmd_vel: v={v:.3f}, w={w:.3f}, d={d:.3f}'
        )

    # -------------------------------------------------------------------------
    # Timer helpers
    # -------------------------------------------------------------------------

    def create_control_timer(self):
        """
        Create the control loop timer using the current control period.
        """

        self.destroy_control_timer()

        self.control_timer = self.create_timer(
            self.control_period,
            self.control_loop
        )

    def destroy_control_timer(self):
        """
        Destroy the control loop timer if it exists.
        """

        if self.control_timer is not None:
            self.destroy_timer(self.control_timer)
            self.control_timer = None

    def recreate_control_timer(self):
        """
        Recreate the control loop timer after frequency change.
        """

        was_enabled = self.controller_enabled

        # Disable during timer replacement to avoid publishing during transition.
        self.controller_enabled = False

        self.destroy_control_timer()
        self.create_control_timer()

        self.controller_enabled = was_enabled

    # -------------------------------------------------------------------------
    # Helper methods
    # -------------------------------------------------------------------------

    def publish_zero_twist(self):
        """
        Publish a zero Twist command if the publisher exists.
        """

        if self.cmd_vel_pub is None:
            return

        cmd = Twist()

        cmd.linear.x = 0.0
        cmd.linear.y = 0.0
        cmd.linear.z = 0.0

        cmd.angular.x = 0.0
        cmd.angular.y = 0.0
        cmd.angular.z = 0.0

        self.cmd_vel_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)

    node = GoToGoalController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard interrupt received.')
    finally:
        node.publish_zero_twist()
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()