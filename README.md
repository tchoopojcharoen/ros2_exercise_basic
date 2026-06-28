# ROS2 Bootcamp — Turtlesim Controller

A hands-on tutorial series for learning ROS2 through turtlesim. You build a working robot controller from scratch, adding capabilities section by section — parameters, services, actions, and lifecycle management — until the system steers a simulated turtle toward any goal you click.

---

## What You Build

Two nodes grow in parallel through the tutorial.

**`circle_publisher`** is the demonstration node. It starts as a minimal publisher that makes the turtle drive in circles, then gains command-line arguments, ROS2 parameters, service clients, a service server, and finally becomes `circle_lf_publisher` — a lifecycle-managed node you can configure, activate, deactivate, and restart without restarting the process.

**`turtle_controller`** is the controller node. It starts as a simple proportional feedback controller (two subscribers, one publisher, one timer) that steers the turtle toward a clicked goal. Over Module 3 it gains parameters, a service server, and finally becomes `turtle_lf_controller` — a lifecycle node with a clean enable/disable model built into the state machine itself.

By the end of Module 3 you also have `fixed_orientation_controller` (an action client) and `goto_goal_action_server` (an action server), and you understand how all three communication patterns — topics, services, and actions — fit together.

---

## Modules

### Module 1 — Basic ROS2 CLIs

Learn the ROS2 concept model and the CLI tools before writing any code. You will use these tools throughout the rest of the tutorial to inspect your nodes.

| Section | Topic |
|---|---|
| 1.1 | What is ROS2? |
| 1.2 | Environment Check & Setup |
| 1.3 | The Computation Graph |
| 1.4 | Topics (CLI) |
| 1.5 | Message Types |
| 1.6 | Services (CLI) |
| 1.7 | Actions (CLI) |
| 1.8 | Parameters (CLI) |
| 1.9 | Remapping and Namespaces |
| 1.10 | Visualising the Computation Graph with rqt_graph |
| 1.11 | Installing ROS2 Packages |
| 1.12 | Module 1 Exercises |

---

### Module 2 — Writing Nodes

Build the `turtlesim_controller` package from nothing. Each section adds one capability; by the end you have a working go-to-goal controller running in real time.

| Section | Topic | What you build |
|---|---|---|
| 2.1 | Creating a ROS2 Workspace | `~/tutorial_ws` with proper overlay structure |
| 2.2 | Creating a Python Package | `turtlesim_controller` with `package.xml`, `setup.py`, `resource/` |
| 2.3 | Your First Node | `HelloNode` — `rclpy.init`, `Node`, `rclpy.spin` |
| 2.4 | Spin and Timers | `HelloPublisher` — `create_timer`, `publish` at a fixed rate |
| 2.5 | Publishing Messages | `circle_publisher` — Twist messages drive the turtle in circles |
| 2.6 | Subscribing to Topics | `pose_reporter` — subscriber callback, subscriber-stores/timer-publishes pattern |
| 2.7 | QoS Profiles | `pose_listener` — diagnosing and fixing a silent subscriber with `ros2 topic info --verbose` |
| 2.8 | Module 2 Exercises | `turtle_controller` — two subscriptions, one publisher, proportional go-to-goal control |

---

### Module 3 — Advanced Nodes

Extend both nodes with the full set of advanced patterns. Each section teaches one concept using the node you already wrote.

| Section | Topic | What you add |
|---|---|---|
| 3.1 | Names and Namespaces | Remapping topics at runtime; understanding the `/` prefix |
| 3.2 | Executable Arguments | `--radius`, `--speed` via `argparse`; `parse_known_args` for ROS2 compatibility |
| 3.3 | ROS2 Parameters | `declare_parameter`, `get_parameter`, parameter callbacks, `ros2 param set` at runtime |
| 3.4 | Service Client | `create_client`, `call_async`, `SetPen` and `TeleportAbsolute` service calls |
| 3.5 | Service Server | `create_service`, `SetBool` server for enabling/disabling the controller |
| 3.6 | Action Client | `fixed_orientation_controller` — `DrawCircles` action with feedback and cancellation |
| 3.7 | Action Server | `goto_goal_action_server` — `GoToGoal` action with progress feedback |
| 3.8 | Lifecycle Nodes | `circle_lf_publisher` and `turtle_lf_controller` — `on_configure`, `on_activate`, `on_deactivate`, `on_shutdown` |

---

## The Final System

The system connects three nodes:

```
turtlesim_node ──► /turtle1/pose ──────────────► turtle_lf_controller
goal_point_publisher ──► /turtle1/goal ─────────► turtle_lf_controller
                                                         │
                                                         ▼
                                 /turtle1/cmd_vel ──► turtlesim_node
```

`turtle_lf_controller` is a lifecycle node. It has no publisher, subscriptions, or timer until it is configured; the control loop only publishes when it is active; deactivating it publishes a zero velocity command to stop the turtle cleanly before going idle.

---

## Prerequisites

- Ubuntu Linux (22.04 or 24.04)
- ROS2 (Humble or Jazzy) installed and sourced
- turtlesim: `sudo apt install ros-<distro>-turtlesim`
- Python 3.10 or later

---

## Repository Structure

```
ros2_tutorial/
├── goal_point_publisher/      # Pre-built helper — GUI node that publishes goal points
├── go_to_goal.py              # Reference lifecycle controller (used in Module 4)
├── module_01_basic_ros2_clis/ # Module 1 markdown files
├── module_02_writing_nodes/   # Module 2 markdown files + control_law.py
│   └── control_law.py         # Proportional go-to-goal function (copy into your package)
├── module_03_advanced_nodes/  # Module 3 markdown files
└── module_04_launch/          # Module 4 markdown files (in progress)
```

**`goal_point_publisher`** is a pre-built PyQt6 GUI node provided to you. You do not modify it. It publishes a `geometry_msgs/msg/Point` on `/turtle1/goal` whenever you click in its window.

**`control_law.py`** is a pure Python function that computes the proportional go-to-goal velocity commands. You copy this into your own package in Module 2 and use it throughout. It has no ROS2 dependency — you can read and test it independently.

---

## Setup

### 1. Install GUI dependencies

```bash
pip install -r goal_point_publisher/requirements.txt
```

### 2. Create the student workspace

The tutorial has you build `turtlesim_controller` from scratch in a separate workspace:

```bash
mkdir -p ~/tutorial_ws/src
cd ~/tutorial_ws/src
```

### 3. Make `goal_point_publisher` available

```bash
cd ~/tutorial_ws/src
ln -s ~/ros2_tutorial/goal_point_publisher .
```

Or copy it:

```bash
cp -r ~/ros2_tutorial/goal_point_publisher ~/tutorial_ws/src/
```

### 4. Build

```bash
cd ~/tutorial_ws
colcon build --packages-select goal_point_publisher
source install/setup.bash
```

You will rebuild frequently as you add nodes. The tutorial reminds you when to rebuild.

---

## Start Here

Open [module_01_basic_ros2_clis/1.1_what_is_ros2.md](module_01_basic_ros2_clis/1.1_what_is_ros2.md).
