# Using ROS2 in Docker Container via WSL

The setup assumes:

* Windows with WSL and WSLg installed
* Docker works from inside WSL
* The Docker image is `osrf/ros:humble-desktop`
* The ROS 2 workspace is located at `~/ros2_ws`
* All ROS 2 terminals use the same Docker container

---

## Internet Connection Requirement

An internet connection is required when:

* Cloning this repository
* Pulling the Docker image
* Installing Linux packages with `apt`
* Installing Python packages with `pip`
* Installing ROS dependencies with `rosdep`

After the image, packages, and dependencies are installed and the workspace is
built, an internet connection is not required to run existing ROS 2 nodes or
launch files locally.

---

# One-Time Windows Setup

## 1. Open WSL

Open PowerShell and run:

```powershell
wsl
```

The remaining commands in this guide should be run inside WSL unless stated
otherwise.

---

## 2. Clone the repository

Clone the `tutorials` branch into your WSL home directory:

```bash
cd ~
git clone -b tutorials https://github.com/tchoopojcharoen/ros2_exercise_basic.git
```

The repository contains the ROS 2 tutorial packages and:

```text
run_docker_ros2_win.sh
```

This script creates or opens the ROS 2 Docker container. Put "run_docker_ros2_win.sh" in the desired location. <locaiton of the file>/run_docker_ros2_win.sh

---

## 3. Create the ROS 2 workspace

The Docker script expects the workspace to be located at `~/ros2_ws`.

Create it:

```bash
mkdir -p ~/ros2_ws/src
```

---

## 4. Verify Docker and WSL graphics

Verify that Docker is available inside WSL:

```bash
docker ps
```

Verify that WSLg has configured the graphical display:

```bash
echo "$DISPLAY"
echo "$WAYLAND_DISPLAY"
```

At least the required WSLg display variables should contain values. If Docker
is unavailable, start Docker Desktop and confirm that WSL integration is
enabled for the current WSL distribution.

---

## 5. Pull the ROS 2 Docker image

```bash
docker pull osrf/ros:humble-desktop
```

This step requires an internet connection.

---

## 6. Make the Docker script executable

```bash
chmod +x <locaiton of the file>/run_docker_ros2_win.sh <session name>
```

This only needs to be done once.

---

# One-Time Container Setup

The following steps must be completed once for the `<session name>` container.
Installed packages and configuration remain available when the container is
stopped and restarted.

## 7. Create and enter the container

```bash
source <locaiton of the file>/run_docker_ros2_win.sh <session name>
```

The script starts one long-running ROS 2 Humble container with:

* WSLg graphics support
* Host networking
* Shared IPC
* `~/ros2_ws` mounted at `/root/ros2_ws`

Always use `session1` in every WSL terminal. The script creates the container
only on the first call. Later calls open additional shells inside that same
container.

---

## 8. Install the required system packages

Inside the container:

```bash
apt update
apt install -y \
  python3-pip \
  libxcb-cursor0
```

The packages provide:

* `python3-pip`: installation of Python dependencies
* `libxcb-cursor0`: the Qt `xcb` platform plugin dependency

Without `libxcb-cursor0`, PyQt6 or Qt may report:

```text
qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin.
```

This step requires an internet connection and only needs to be completed once
for the container.

---

## 9. Configure the container environment

Inside the container, add the ROS 2 environment configuration to `~/.bashrc`:

```bash
cat >> ~/.bashrc <<'EOF'

source /opt/ros/humble/setup.bash

if [ -f /root/ros2_ws/install/setup.bash ]; then
    source /root/ros2_ws/install/setup.bash
fi
EOF
```

Reload the configuration:

```bash
source ~/.bashrc
```

This configuration only needs to be added once. Do not repeatedly append the
same block to `~/.bashrc`.

---

# Daily Workflow

## 10. Open WSL

Open PowerShell and run:

```powershell
wsl
```

Make sure Docker Desktop is running.

---

## 11. Enter the existing ROS 2 container

Inside WSL:

```bash
source <locaiton of the file>/run_docker_ros2_win.sh <session name>
```

The script starts `session1` if it is stopped and opens a shell inside it.

For every additional WSL terminal, run the same command:

```bash
source <locaiton of the file>/run_docker_ros2_win.sh <session name>
```

Do not use another session name. A different name would create another
container, and its ROS 2 nodes may not communicate with the nodes in
`session1`.

---
# Test the Setup

## 12. Run turtlesim

In the first container terminal:

```bash
ros2 run turtlesim turtlesim_node
```

The turtlesim window should appear through WSLg.

Open another WSL terminal and enter the same container:

```bash
source <locaiton of the file>/run_docker_ros2_win.sh <session name>
```

Run the keyboard controller:

```bash
ros2 run turtlesim turtle_teleop_key
```

Keep the second terminal focused and use the arrow keys to move the turtle.

Both commands must run in `session1` so that the ROS 2 nodes share the same
container and network environment.

---

# Notes About the Docker Script

The script:

```text
run_docker_ros2_win.sh
```

must create `<session name>` as a long-running container on its first invocation.
When `session1` already exists, it must start it if necessary and use
`docker exec` to open a new shell inside it.

Use:

```bash
source <locaiton of the file>/run_docker_ros2_win.sh <session name>
```

for every ROS 2 terminal.

Do not repeatedly use `docker run`, because that creates separate containers.
