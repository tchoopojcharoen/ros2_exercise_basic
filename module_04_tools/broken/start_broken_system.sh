#!/bin/bash
# Start the broken go-to-goal system for the Module 4 capstone.
#
# Launches turtlesim, goal_point_publisher, and the broken lifecycle controller,
# then configures and activates the controller.  The system will appear to run
# (no crashes, no error messages) but the turtle will not move toward goals.
#
# Usage: bash start_broken_system.sh
# Stop:  Ctrl+C kills all background processes.

source /opt/ros/humble/setup.bash
source ~/tutorial_ws/install/setup.bash

cleanup() {
    echo ""
    echo "Stopping all processes..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}
trap cleanup INT TERM

echo "Starting turtlesim..."
ros2 run turtlesim turtlesim_node &
sleep 1

echo "Starting goal_point_publisher..."
ros2 run goal_point_publisher goal_point_publisher &
sleep 1

echo "Starting broken controller..."
ros2 run turtlesim_controller turtle_lf_controller_broken &
sleep 2

echo "Configuring and activating broken controller..."
ros2 lifecycle set /turtle_lf_controller_broken configure
ros2 lifecycle set /turtle_lf_controller_broken activate

echo ""
echo "System is running. Press Ctrl+C to stop all processes."
echo ""
echo "Symptom: clicking goal points does not cause the turtle to move."
echo "Use the tools from sections 4.1-4.3 to diagnose and fix the problem."

wait
