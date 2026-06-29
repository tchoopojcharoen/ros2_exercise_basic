# Using ROS 2 in a Docker Container on Linux

The setup assumes:

* Linux with an X11 display or XWayland
* Docker is installed and available to the current user
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

# One-Time Linux Setup

## 1. Clone the repository

Open a terminal and clone the `tutorials` branch:

```bash
cd ~
git clone -b tutorials https://github.com/tchoopojcharoen/ros2_exercise_basic.git
```

The repository contains the ROS 2 tutorial packages and:

```text
run_docker_ros2_linux.sh
```

This script creates or opens the ROS 2 Docker container. Place
`run_docker_ros2_linux.sh` in the desired location:

```text
<location of the file>/run_docker_ros2_linux.sh
```

---

## 2. Create the ROS 2 workspace

The Docker script expects the workspace to be located at `~/ros2_ws`.

Create it:

```bash
mkdir -p ~/ros2_ws/src
```

If a different workspace location is used, update the workspace path inside
`run_docker_ros2_linux.sh`.

---

## 3. Verify Docker

Check that Docker is available:

```bash
docker ps
```

If Docker reports a permission error, add the current user to the `docker`
group:

```bash
sudo usermod -aG docker "$USER"
```

Log out of Linux and log back in before checking again:

```bash
docker ps
```

---

## 4. Configure graphical access

Verify that the host display is configured:

```bash
echo "$DISPLAY"
```

The output should normally resemble:

```text
:0
```

Allow the root user inside the local Docker container to access the display:

```bash
xhost +SI:localuser:root
```

Expected output resembles:

```text
localuser:root being added to access control list
```

This is more restricted than disabling X11 access control with `xhost +`.

Run the `xhost` command again after restarting the graphical session if GUI
applications can no longer connect to the display.

---

## 5. Pull the ROS 2 Docker image

```bash
docker pull osrf/ros:humble-desktop
```

This step requires an internet connection.

---

## 6. Make the Docker script executable

```bash
chmod +x <location of the file>/run_docker_ros2_linux.sh
```

Replace `<location of the file>` with the actual directory containing the
script. Do not include the session name in the `chmod` command.

This only needs to be done once.

---

# One-Time Container Setup

The following steps must be completed once for the `<session name>` container.
Installed packages and configuration remain available when the container is
stopped and restarted.

## 7. Create and enter the container

Choose one session name and use it consistently. For example:

```bash
source <location of the file>/run_docker_ros2_linux.sh session1
```

The script starts one long-running ROS 2 Humble container with:

* Linux X11 graphics support
* Host networking
* Shared IPC
* `~/ros2_ws` mounted at `/root/ros2_ws`

Always use `session1` in every terminal. The script creates the container only
on the first call. Later calls open additional shells inside the same
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

## 10. Verify Docker and graphical access

Check that Docker is running:

```bash
docker ps
```

Allow the container to access the host display:

```bash
xhost +SI:localuser:root
```

---

## 11. Enter the existing ROS 2 container

Run:

```bash
source <location of the file>/run_docker_ros2_linux.sh session1
```

The script starts `session1` if it is stopped and opens a shell inside it.

For every additional terminal, run the same command:

```bash
source <location of the file>/run_docker_ros2_linux.sh session1
```

Do not use another session name. A different name would create another
container.

Using the same container also avoids unnecessary DDS discovery and networking
differences between separate containers.

---

# Test the Setup

## 12. Run turtlesim

In the first container terminal:

```bash
ros2 run turtlesim turtlesim_node
```

The turtlesim window should appear on the Linux desktop.

Open another Linux terminal and enter the same container:

```bash
source <location of the file>/run_docker_ros2_linux.sh session1
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
run_docker_ros2_linux.sh
```

must create `<session name>` as a long-running container on its first
invocation. When that container already exists, the script must start it if
necessary and use `docker exec` to open a new shell inside it.

Use:

```bash
source <location of the file>/run_docker_ros2_linux.sh session1
```

for every ROS 2 terminal.

Do not repeatedly use `docker run`, because that creates separate containers.

The Linux container should use:

* `--network host` for native host networking
* `--ipc host` for shared IPC
* `DISPLAY` from the Linux host
* `/tmp/.X11-unix` mounted into the container
* `~/ros2_ws` mounted at `/root/ros2_ws`
