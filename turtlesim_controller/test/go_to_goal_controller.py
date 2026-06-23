import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from geometry_msgs.msg import Twist, Point
from turtlesim.msg import Pose
import math

class GoToGoalController():
    def __init__(self,period:float=0.1,Kv:float=1.0,Kw:float = 5.0):
        self.pose = None
        self.goal = None
        self.gain = [Kv,Kw]
        self.period = period
        self.tolerance = 0.01
    def pose_update(self,x,y,theta):
        self.pose = [x,y,theta]
    def goal_update(self,x,y):
        self.goal = [x,y]
    def compute(self):
        v = 0.0
        w = 0.0
        if self.pose and self.goal:
            pos_diff = [self.goal[i]-self.pose[i] for i in range(2)]
            d = math.sqrt(pos_diff[0]**2+pos_diff[1]**2)
            if d>self.tolerance:
                v = self.gain[0]*d
                de = math.atan2(pos_diff[1],pos_diff[0])-self.pose[2]
                w = self.gain[1]*math.atan2(math.sin(de),math.cos(de))
        return v,w
    
class GoToGoalROSInterface():
    def __init__(self,namespace='turtle1'):
        self.node = Node('turtlesim_go_to_goal')
        self.controller = GoToGoalController(period=0.1)
        self.cmd_vel_pub = self.node.create_publisher(Twist,'/'+namespace+'/cmd_vel',1)
        update_pose = lambda msg: self.controller.pose_update(msg.x,msg.y,msg.theta)
        update_goal = lambda msg: self.controller.goal_update(msg.x,msg.y)
        self.node.create_subscription(Pose,'/'+namespace+'/pose',update_pose,1)
        self.node.create_subscription(Point,'/'+namespace+'/goal',update_goal,1)
        self.node.create_timer(self.controller.period,self.timer_callback)
    #def pose_callback(self,msg:Pose):
    #    self.controller.pose_update(msg.x,msg.y,msg.theta)
    #def goal_callback(self,msg:Point):
    #    self.controller.goal_update(msg.x,msg.y)
    def timer_callback(self):
        v,w = self.controller.compute()
        msg = Twist()
        msg.linear.x = v
        msg.angular.z = w
        self.cmd_vel_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    ros_interface = GoToGoalROSInterface()

    rclpy.spin(ros_interface.node)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    ros_interface.node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()