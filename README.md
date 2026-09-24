# ROS 2 Basic Bootcamp 

A hands-on tutorial series for learning ROS 2 through turtlesim. You start with the command-line tools, write a Python package from scratch, add parameters, services, actions, and lifecycle management, learn the tools professionals use to debug and record a running system, and finish by launching the whole system with a single command. The result steers a simulated turtle toward any goal you click.

The tutorial has five modules, about 50 sections in total. Each section is a short markdown file with learning objectives, worked steps, an exercise with an answer key, and a verification checklist.

---

## What You Build

Two nodes grow in parallel through Modules 2 and 3.

**`circle_publisher`** is the demonstration node. It starts as a minimal publisher that makes the turtle drive in circles, then gains command-line arguments, ROS 2 parameters, and service clients, and finally becomes `circle_lf_publisher`, a lifecycle-managed node you can configure, activate, deactivate, and restart without restarting the process.

**`turtle_controller`** is the controller node. It starts as a simple proportional feedback controller (two subscribers, one publisher, one timer) that steers the turtle toward a clicked goal. Over Module 3 it gains parameters and a service server, and finally becomes `turtle_lf_controller`, a lifecycle node whose enable/disable model is built into the state machine itself.

Module 3 also adds `fixed_orientation_controller` (an action client) and `goto_goal_action_server` (an action server), so you meet all three communication patterns — topics, services, and actions — in working code.

Module 4 gives you the tools to inspect, measure, record, and visualize this system, and ends with a lab where you diagnose a deliberately broken controller. Module 5 replaces the many terminals and manual commands with launch files.

---

## Modules

| Module | Focus | You finish with |
|---|---|---|
| [1 — Basic ROS 2 CLIs](#module-1--basic-ros-2-clis) | Concepts and command-line tools | Fluency with `ros2 topic`, `service`, `action`, `param`, `rqt_graph` |
| [2 — Writing Nodes](#module-2--writing-nodes) | Python nodes with `rclpy` | A workspace, a package, and a working go-to-goal controller |
| [3 — Advanced Nodes](#module-3--advanced-nodes) | Arguments, parameters, services, actions, lifecycle | `turtle_lf_controller`, an action client and server |
| [4 — Tools](#module-4--tools-observation-debugging-and-visualization) | Observing, debugging, recording, visualizing | Debugged a broken system using the tools |
| [5 — Launch](#module-5--launch-engineering) | Launch files | One command that starts and activates the full system |

### Module 1 — Basic ROS 2 CLIs

Learn the ROS 2 concept model and the CLI tools before writing any code. You use these tools throughout the rest of the tutorial to inspect your nodes.

| Section | Topic |
|---|---|
| 1.1 | What is ROS 2? |
| 1.2 | Environment Check & Setup |
| 1.3 | The Computation Graph |
| 1.4 | Topics (CLI) |
| 1.5 | Message Types |
| 1.6 | Services (CLI) |
| 1.7 | Actions (CLI) |
| 1.8 | Parameters (CLI) |
| 1.9 | Remapping and Namespaces |
| 1.10 | Visualising the Computation Graph with rqt_graph |
| 1.11 | Installing ROS 2 Packages |
| 1.12 | Module 1 Exercises |

### Module 2 — Writing Nodes

Build the `turtlesim_controller` package from nothing. Each section adds one capability; by the end you have a working go-to-goal controller running in real time.

| Section | Topic | What you build |
|---|---|---|
| 2.1 | Creating a ROS 2 Workspace | `~/tutorial_ws` with proper overlay structure |
| 2.2 | Creating a Python Package | `turtlesim_controller` with `package.xml`, `setup.py`, `resource/` |
| 2.3 | Your First Node | `HelloNode` — `rclpy.init`, `Node`, `rclpy.spin` |
| 2.4 | Spin and Timers | `HelloPublisher` — `create_timer`, `publish` at a fixed rate |
| 2.5 | Publishing Messages | `circle_publisher` — Twist messages drive the turtle in circles |
| 2.6 | Subscribing to Topics | `pose_reporter` — subscriber callback, subscriber-stores/timer-publishes pattern |
| 2.7 | QoS Profiles | `pose_listener` — diagnosing and fixing a silent subscriber with `ros2 topic info --verbose` |
| 2.8 | Module 2 Exercises | `turtle_controller` — two subscriptions, one publisher, proportional go-to-goal control |

### Module 3 — Advanced Nodes

Extend both nodes with the full set of advanced patterns. Each section teaches one concept using a node you already wrote.

| Section | Topic | What you add |
|---|---|---|
| 3.1 | Names and Namespaces | Remapping topics at runtime; understanding the `/` prefix |
| 3.2 | Executable Arguments | `--radius`, `--speed` via `argparse`; `parse_known_args` for ROS 2 compatibility |
| 3.3 | ROS 2 Parameters | `declare_parameter`, `get_parameter`, parameter callbacks, `ros2 param set` at runtime |
| 3.4 | Service Client | `create_client`, `call_async`, `SetPen` and `TeleportAbsolute` service calls |
| 3.5 | Service Server | `create_service`, `SetBool` server for enabling/disabling the controller |
| 3.6 | Action Client | `fixed_orientation_controller` — `DrawCircles` action with feedback and cancellation |
| 3.7 | Action Server | `goto_goal_action_server` — `GoToGoal` action with progress feedback |
| 3.8 | Lifecycle Nodes | `circle_lf_publisher` and `turtle_lf_controller` — `on_configure`, `on_activate`, `on_deactivate`, `on_shutdown` |

### Module 4 — Tools: Observation, Debugging, and Visualization

Learn the toolkit used to inspect running systems, diagnose problems, record data, and visualize robot state. All exercises use the system built in Modules 1–3.

| Section | Topic |
|---|---|
| 4.1 | ROS Graph and Message Introspection — `rqt_topic`, `rqt_service_caller`, hidden nodes |
| 4.2 | Logging and System Diagnosis — `rqt_console`, `/rosout`, runtime log levels, `ros2 doctor` |
| 4.3 | Communication Measurement and QoS Diagnosis — `ros2 topic delay`, `header.stamp`, `frame_id`, `use_sim_time`, QoS mismatch workflow |
| 4.4 | Recording and Replaying with rosbag2 — `ros2 bag record/play/info/convert` |
| 4.5 | Plotting Numerical Data — `rqt_plot`, PlotJuggler (optional) |
| 4.6 | Coordinate Frames and TF2 — `static_transform_publisher`, `tf2_echo`, `view_frames`, `rqt_tf_tree`, TF error diagnosis |
| 4.7 | Visualization with RViz2 — fixed frame, TF display, `.rviz` config files |
| 4.8 | Robot Health and Diagnostics — `diagnostic_updater`, `/diagnostics` topic, `rqt_robot_monitor` (optional) |
| 4.9 | Capstone: Debugging a Broken System — an integrated lab using the tools from 4.1–4.3 |
| 4.10 | Modern and Advanced Tools (optional) — `topic_tools`, Foxglove Studio, `ros2_tracing` |

### Module 5 — Launch Engineering

Start multiple nodes from a single command, configure them with YAML and arguments, compose launch files, react to events, and automate lifecycle transitions on startup. This replaces the bash script used in the Module 4 capstone.

| Section | Topic |
|---|---|
| 5.1 | What Is a Launch File? — `generate_launch_description`, `Node`, installing with `data_files` |
| 5.2 | Multiple Nodes: Namespaces, Remapping, Parameters |
| 5.3 | YAML Parameter Files |
| 5.4 | Parameters in Launch — layering, `FindPackageShare`, `arguments=` |
| 5.5 | Launch Arguments — `DeclareLaunchArgument`, `LaunchConfiguration` |
| 5.6 | IncludeLaunchDescription |
| 5.7 | OpaqueFunction — using argument values as Python values |
| 5.8 | Conditions — `IfCondition`, `UnlessCondition`, `PythonExpression` |
| 5.9 | Event Handlers — running or shutting down nodes when other nodes start, exit, or print |
| 5.10 | Lifecycle Transitions in Launch — `LifecycleNode`, `ChangeState`, `OnStateTransition` |
| 5.11 | Module 5 Exercises — the final `go_to_goal.launch.py` |

---

## The Final System

At the end of Module 5, one command starts three nodes and brings the controller to `active`:

```bash
ros2 launch turtlesim_controller go_to_goal.launch.py
```

```
turtlesim_node ──► /turtle1/pose ──► turtle_lf_controller
goal_point_publisher ──► /goal ────► turtle_lf_controller
                                              │
                                              ▼
                       /turtle1/cmd_vel ──► turtlesim_node
```

`turtle_lf_controller` is a lifecycle node. It has no publisher, subscriptions, or timer until it is configured; the control loop only publishes when it is active; deactivating it publishes a zero velocity command to stop the turtle cleanly before going idle. The launch file configures and activates it for you, and exposes the gains `Kv`, `Kw`, and the loop `frequency` as launch arguments.

---

## Prerequisites

- Ubuntu Linux (22.04 for Humble, 24.04 for Jazzy), or the Windows/macOS setups below
- ROS 2 installed and sourced. The tutorial's commands and paths use **Humble**; on Jazzy, replace `humble` with `jazzy`
- turtlesim: `sudo apt install ros-<distro>-turtlesim`
- Python 3.10 or later
- Basic Python: classes, functions, and imports. No prior ROS experience is needed

---

## How Each Section Works

- **Terminals.** Commands are meant to be typed into a terminal, not run from the markdown file. Sections tell you how many terminals to open, and every new terminal must be sourced (`source /opt/ros/humble/setup.bash` and `source ~/tutorial_ws/install/setup.bash`)
- **Before You Begin.** Each section lists what it builds on and what you need running
- **Exercises and answer keys.** Try each exercise before opening the answer key at the end of the section
- **Verification checklist.** Each section ends with a checklist of observable results. Do not move on until each item is true
- **Stop All Processes.** Sections end with a reminder to stop what you started, so the next section begins from a clean state
- **Rebuild reminders.** After adding a node, launch file, or config file, run `colcon build --packages-select turtlesim_controller` and source the workspace again. The tutorial reminds you when

---

## Repository Structure

```
ros2_tutorial/
├── goal_point_publisher/       # Pre-built helper — GUI node that publishes goal points
├── module_01_basic_ros2_clis/  # Module 1 markdown files
├── module_02_writing_nodes/    # Module 2 markdown files + control_law.py
│   └── control_law.py          # Proportional go-to-goal function (copy into your package)
├── module_03_advanced_nodes/   # Module 3 markdown files
├── module_04_tools/            # Module 4 markdown files + capstone support files
│   └── broken/                 # Broken node and setup script for the capstone lab
└── module_05_launch/           # Module 5 markdown files
```

The `turtlesim_controller` package is **not** in this repository. You create it yourself in `~/tutorial_ws/src` starting in Module 2.

**`goal_point_publisher`** is a pre-built PyQt6 GUI node provided to you. You do not modify it. It publishes a `geometry_msgs/msg/Point` on the relative topic `goal` whenever you click in its window.

**`control_law.py`** is a pure Python function that computes the proportional go-to-goal velocity commands. You copy it into your own package in Module 2 and use it throughout. It has no ROS 2 dependency, so you can read and test it independently.

**`module_04_tools/broken/`** holds `turtle_lf_controller_broken.py` and `start_broken_system.sh`, used only by the Module 4 capstone (4.9).

---

## Setup

### 1. Install GUI dependencies

```bash
pip install -r goal_point_publisher/requirements.txt
```

### 2. Create the student workspace

```bash
mkdir -p ~/tutorial_ws/src
cd ~/tutorial_ws/src
```

### 3. Make `goal_point_publisher` available

Link it:

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

---

## Windows and macOS Users

Do not worry. Follow [SETUP_WIN.md](SETUP_WIN.md) or [SETUP_MAC.md](SETUP_MAC.md) to run a Linux subsystem or a Docker container with ROS 2 Humble pre-installed. Once you are comfortable opening multiple terminals in that setup, follow the tutorial as normal.

---

## Start Here

Open [module_01_basic_ros2_clis/1.1_what_is_ros2.md](module_01_basic_ros2_clis/1.1_what_is_ros2.md).
