## Using ROS2 in Docker Container via Colima

The setup assumes:

* macOS with Colima and Docker installed
* XQuartz is used to display Linux GUI applications
* The Docker image is `osrf/ros:humble-desktop-full`
* The ROS 2 workspace is located at `~/ros2_ws`
* All ROS 2 terminals use the same Docker container

---

## Internet Connection Requirement

An internet connection is required when:

* Cloning this repository
* Pulling the Docker image
* Installing Linux packages with `apt`

After the image and required packages are installed, an internet connection is
not required to run existing ROS 2 nodes or launch files locally.

---

# One-Time Mac Setup

## 1. Clone the repository

Clone the `tutorials` branch into your home directory:

```bash
cd ~
git clone -b tutorials https://github.com/tchoopojcharoen/ros2_exercise_basic.git
```

The repository contains the ROS 2 tutorial packages and:

```text
run_docker_ros2_mac.sh
```

This script creates or opens the ROS 2 Docker container.

---

## 2. Create the ROS 2 workspace

The Docker script expects the workspace to be located at `~/ros2_ws`.

Create it:

```bash
mkdir -p ~/ros2_ws/src
```

Move the repository contents into the workspace:

```bash
cp -R ~/ros2_exercise_basic/. ~/ros2_ws/src/
rm -rf ~/ros2_exercise_basic
```

The workspace should now resemble:

```text
~/ros2_ws/
└── src/
    ├── run_docker_ros2_mac.sh
    ├── README.md
    ├── <ros2_package_1>/
    └── <ros2_package_2>/
```

If a different workspace location is used, update the workspace path inside
`run_docker_ros2_mac.sh`.

---

## 3. Install and configure XQuartz

Install XQuartz:

```bash
brew install --cask xquartz
```

After installation, close the current Terminal window and open a new one.
An already-open terminal may not detect the XQuartz commands and may report:

```text
xhost: command not found
```

Verify that `xhost` is installed:

```bash
/opt/X11/bin/xhost -help
```

Enable network connections:

```bash
defaults write org.xquartz.X11 nolisten_tcp -bool false
```

Restart XQuartz:

```bash
killall XQuartz 2>/dev/null
open -a XQuartz
```

Wait a few seconds, then set the display and allow local connections:

```bash
export DISPLAY=:0
/opt/X11/bin/xhost +localhost
/opt/X11/bin/xhost +127.0.0.1
```

Expected output resembles:

```text
localhost being added to access control list
127.0.0.1 being added to access control list
```

Setting `DISPLAY=:0` prevents this error:

```text
xhost: unable to open display ""
```

Using `/opt/X11/bin/xhost` directly also works when `xhost` has not yet been
added to `PATH`.

---

## 4. Start Colima

```bash
colima start
```

Verify that Colima and Docker are running:

```bash
colima status
docker ps
```

---

## 5. Pull the ROS 2 Docker image

```bash
docker pull osrf/ros:humble-desktop-full
```

This step requires an internet connection.

---

## 6. Make the Docker script executable

```bash
chmod +x ~/ros2_ws/src/run_docker_ros2_mac.sh
```

This only needs to be done once.

---

# One-Time Container Setup

The following steps must be completed once for each new named container.
Installed packages and configuration remain available when that container is
stopped and restarted. If the container is removed, the following steps must be performed gain.

## 7. Create and enter the container

Choose a session name, such as `session1`:

```bash
source ~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

The script starts a long-running ROS 2 Humble container with:

* XQuartz graphics support
* CycloneDDS environment settings
* Localhost-only ROS 2 discovery
* `~/ros2_ws` mounted at `/root/ros2_ws`

Use the same session name in every terminal.

---

## 8. Install the required packages

Inside the container:

```bash
apt update
apt install -y \
  python3-pip \
  libxcb-cursor0 \
  ros-humble-rmw-cyclonedds-cpp
```

The packages provide:

* `python3-pip`: installation of Python dependencies
* `libxcb-cursor0`: the Qt `xcb` platform plugin dependency
* `ros-humble-rmw-cyclonedds-cpp`: CycloneDDS support for ROS 2

CycloneDDS avoids the DDS discovery problem encountered with the default
middleware under Colima.

This step requires an internet connection and only needs to be completed once
per container.

---

## 9. Configure the container environment

Add the ROS 2 configuration to the container's `~/.bashrc`:

```bash
cat >> ~/.bashrc <<'EOF'

source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0
export ROS_LOCALHOST_ONLY=1
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export DISPLAY=host.docker.internal:0
export QT_X11_NO_MITSHM=1
export LIBGL_ALWAYS_SOFTWARE=1

if [ -f /root/ros2_ws/install/setup.bash ]; then
    source /root/ros2_ws/install/setup.bash
fi
EOF
```

Reload the configuration:

```bash
source ~/.bashrc
```

Verify it:

```bash
echo "$RMW_IMPLEMENTATION"
echo "$ROS_LOCALHOST_ONLY"
echo "$DISPLAY"
```

Expected output:

```text
rmw_cyclonedds_cpp
1
host.docker.internal:0
```

`ROS_LOCALHOST_ONLY=1` is appropriate because every ROS 2 node runs inside the
same container. It also avoids unsupported multicast behavior under Colima.

This configuration only needs to be added once per container. Do not repeatedly
append the same block to `~/.bashrc`.

---

# Daily Workflow

## 10. Start XQuartz

On macOS:

```bash
killall XQuartz 2>/dev/null
open -a XQuartz
```

Wait a few seconds, then run:

```bash
export DISPLAY=:0
/opt/X11/bin/xhost +localhost
/opt/X11/bin/xhost +127.0.0.1
```

Repeat this step after restarting XQuartz or macOS.

---

## 11. Start Colima

Run this in the first terminal:

```bash
colima start
```

If Colima is already running, the command will report that it is running.

---

## 12. Enter the ROS 2 container

Use the same session name that was used during container setup:

```bash
source ~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

The script starts the existing container if necessary and opens a shell inside
it.

For every additional terminal, run the same command:

```bash
source ~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

Do not use a different session name unless a separate container is intended.

---

# Test the Setup

## 13. Run turtlesim

In the first container terminal:

```bash
ros2 run turtlesim turtlesim_node
```

The turtlesim window should appear through XQuartz.

Open another macOS terminal and enter the same container:

```bash
source ~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

Run the keyboard controller:

```bash
ros2 run turtlesim turtle_teleop_key
```

Keep the second terminal focused and use the arrow keys to move the turtle.

Both commands must use the same container session so that the ROS 2 nodes can
discover each other.
