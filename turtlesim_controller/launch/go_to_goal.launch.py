#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import EmitEvent
from launch.actions import RegisterEventHandler
from launch_ros.actions import Node
from launch_ros.actions import LifecycleNode
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState

from lifecycle_msgs.msg import Transition


def generate_launch_description():
    turtle_namespace = 'turtle1'

    turtlesim_node = Node(
        package='turtlesim',
        executable='turtlesim_node',
        name='turtlesim',
        output='screen',
    )

    goal_point_publisher_node = Node(
        package='goal_point_publisher',
        executable='goal_point_publisher',
        name='goal_point_publisher',
        namespace=turtle_namespace,
        output='screen',
    )

    go_to_goal_controller_node = LifecycleNode(
        package='turtlesim_controller',
        executable='go_to_goal_controller',
        name='go_to_goal_controller',
        namespace=turtle_namespace,
        output='screen',
        parameters=[
            {
                'kv': 1.0,
                'kw': 5.0,
                'tolerance': 0.01,
                'control_loop_frequency': 10.0,
            }
        ],
    )

    configure_go_to_goal_controller = EmitEvent(
        event=ChangeState(
            lifecycle_node_matcher=lambda node: node == go_to_goal_controller_node,
            transition_id=Transition.TRANSITION_CONFIGURE,
        )
    )

    activate_go_to_goal_controller = RegisterEventHandler(
        OnStateTransition(
            target_lifecycle_node=go_to_goal_controller_node,
            goal_state='inactive',
            entities=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=lambda node: node == go_to_goal_controller_node,
                        transition_id=Transition.TRANSITION_ACTIVATE,
                    )
                )
            ],
        )
    )

    return LaunchDescription([
        turtlesim_node,
        goal_point_publisher_node,
        go_to_goal_controller_node,

        # Automatically configure and activate the lifecycle controller.
        activate_go_to_goal_controller,
        configure_go_to_goal_controller,
    ])