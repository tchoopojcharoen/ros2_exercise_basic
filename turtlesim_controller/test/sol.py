import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist, Point
from turtlesim.msg import Pose
from turtlesim_controller.control_law import compute_go_to_goal_control


class GoToGoalNode(Node):
    def __init__(self):
        super().__init__('go_to_goal')

        # Store the current turtle pose and desired goal position.
        self.pose = None
        self.goal = None

        # Declare ROS parameters with default values.
        self.declare_parameter('Kv', 1.0)
        self.declare_parameter('Kw', 5.0)
        self.declare_parameter('tolerance', 0.01)

        # Timer period in seconds.
        self.period = 0.1

        # Publisher for sending velocity commands to turtlesim.
        self.cmd_vel_pub = self.create_publisher(Twist,'cmd_vel',10)

        # Subscriber for receiving the current turtle pose.
        self.pose_sub = self.create_subscription(Pose,'pose',self.pose_callback,10)

        # Subscriber for receiving the goal position.
        self.goal_sub = self.create_subscription(Point,'goal',self.goal_callback,10)

        # Timer for repeatedly computing and publishing velocity commands.
        self.timer = self.create_timer(self.period,self.timer_callback)

    def pose_callback(self, msg: Pose):
        """
        Callback function for the turtle pose subscriber.

        This function is called every time a new Pose message is received.
        """

        self.pose = [msg.x, msg.y, msg.theta]

    def goal_callback(self, msg: Point):
        """
        Callback function for the goal subscriber.

        This function is called every time a new Point message is received.
        """

        self.goal = [msg.x, msg.y]

    def timer_callback(self):
        """
        Timer callback function.

        This function is called repeatedly at the timer period.
        It reads the latest parameter values, computes the control input,
        and publishes a Twist message.
        """

        # Read the latest parameter values every timer loop.
        Kv = self.get_parameter('Kv').value
        Kw = self.get_parameter('Kw').value
        tolerance = self.get_parameter('tolerance').value

        v, w = compute_go_to_goal_control(
            self.pose,
            self.goal,
            Kv,
            Kw,
            tolerance
        )

        msg = Twist()
        msg.linear.x = v
        msg.angular.z = w

        self.cmd_vel_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    node = GoToGoalNode()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()