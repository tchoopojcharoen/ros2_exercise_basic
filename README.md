# ROS 2 Bootcamp — Turtlesim Go-to-Goal Controller

A hands-on bootcamp exercise that teaches ROS 2 fundamentals by having students build a working robot controller from scratch.

## Overview

This project is the capstone exercise of a ROS 2 bootcamp. Students build the `turtlesim_controller` package incrementally over the course of the bootcamp — this repository contains the **final solution**.

The exercise uses the turtlesim simulator, a lightweight 2D robot simulator built into ROS 2, as a safe and visual environment to practice real robotics software patterns. By the time a student has completed the exercise, they have written every piece of the system themselves and understand how it all connects.

## What the Final System Does

Launching the project opens two windows side by side: the turtlesim simulator and an interactive goal-setting GUI.

In the GUI, you click or drag anywhere on a 2D field to set a goal position. The turtle in the simulator immediately begins moving toward that point. It follows a smooth arc — turning to face the goal, then driving forward — and stops precisely when it arrives. You can set a new goal at any time, change coordinates by typing them in, or switch to periodic mode to have goals published automatically at a configurable rate.

The system is made up of three nodes working together:

- The **goal publisher** (`goal_point_publisher`) provides the GUI and continuously broadcasts the current goal position to the rest of the system over a ROS 2 topic.
- The **controller** (`turtlesim_controller`) subscribes to that goal and to the turtle's live position, computes the velocity commands needed to close the gap, and publishes them at a fixed control rate. It is implemented as a lifecycle node, meaning it has explicit states for configured, active, and inactive — making startup and shutdown predictable and safe. The full system launches automatically from unconfigured to active without any manual intervention.
- The **turtlesim simulator** (a standard ROS 2 package) executes the velocity commands and reports the turtle's updated position back to the controller on every tick.

## Repository Structure

```
ros2_tutorial/
├── turtlesim_controller/    # The exercise package — what students build
└── goal_point_publisher/    # Pre-built helper package — provided to students
```

**`turtlesim_controller`** is the exercise deliverable. It contains the go-to-goal controller and a launch file that starts the full three-node system with a single command. Students build this package from scratch over the bootcamp.

**`goal_point_publisher`** is a pre-built helper provided to students. It is intentionally kept as a separate, independent package so that it can be reused across different projects and so that students can focus on the controller logic without getting distracted by GUI code.

## Prerequisites

- Ubuntu Linux
- ROS 2 (Jazzy or compatible) installed and sourced in your shell
- turtlesim: `sudo apt install ros-<distro>-turtlesim`

## Quick Start

**1. Install Python dependencies**

```bash
pip install -r goal_point_publisher/requirements.txt
```

**2. Build both packages**

```bash
colcon build
```

**3. Source the workspace**

```bash
source install/setup.bash
```

**4. Launch the full system**

```bash
ros2 launch turtlesim_controller go_to_goal.launch.py
```

The turtlesim window and the goal publisher GUI will open automatically. Click anywhere on the field in the GUI to send the turtle to a new goal.

## Learning Outcomes

After completing the bootcamp exercise, students are able to:

- Create and build a ROS 2 Python package from scratch using the ament build system
- Write nodes that publish and subscribe to topics, with appropriate QoS settings
- Use a timer to run a control loop at a fixed frequency
- Declare and read ROS 2 parameters, and respond to parameter changes at runtime
- Implement a lifecycle node that transitions cleanly through configured, inactive, and active states
- Write a launch file that starts multiple nodes and automates lifecycle transitions
- Reason about a multi-node computation graph and trace how data flows between nodes
