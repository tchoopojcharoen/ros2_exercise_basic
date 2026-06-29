# ROS 2 Basic Exercise

This repository contains basic ROS 2 packages and a helper script for running
ROS 2 Humble inside Docker on macOS with Colima.

The setup assumes:

* macOS with Colima and Docker installed
* XQuartz is used to display Linux GUI applications
* The Docker image used is `osrf/ros:humble-desktop-full`
* A ROS 2 workspace is located at `~/ros2_ws`
* All ROS 2 terminals use the same Docker container

---

## Internet Connection Requirement

An internet connection is required when:

* Cloning this repository
* Pulling the Docker image
* Installing Linux packages with `apt`
* Installing Python packages with `pip`
* Installing ROS dependencies with `rosdep`

After all required packages are installed and the workspace has been built, an
internet connection is **not required** to run existing ROS 2 nodes or launch
files locally.

---

## 1. Start Colima

Open Terminal on macOS and run:

```bash
colima start
```

Verify that Colima and Docker are running:

```bash
colima status
docker ps
```

---

## 2. Install and configure XQuartz

Install XQuartz:

```bash
brew install --cask xquartz
```

Enable XQuartz network connections:

```bash
defaults write org.xquartz.X11 nolisten_tcp -bool false
```

Restart XQuartz:

```bash
killall XQuartz 2>/dev/null
open -a XQuartz
```

In XQuartz, open:

```text
XQuartz > Settings > Security
```

Enable:

```text
Allow connections from network clients
```

Restart XQuartz again:

```bash
killall XQuartz
open -a XQuartz
```

Allow local connections:

```bash
xhost +localhost
xhost +127.0.0.1
```

Run the two `xhost` commands again after restarting XQuartz or macOS.

---

## 3. Create a ROS 2 workspace

```bash
cd ~
mkdir -p ~/ros2_ws/src
```

---

## 4. Clone this repository

Clone the repository into your home directory:

```bash
cd ~
git clone -b main https://github.com/tchoopojcharoen/ros2_exercise_basic.git
```

Move the repository contents into the ROS 2 workspace `src` folder:

```bash
mv ros2_exercise_basic/* ~/ros2_ws/src/
rm -rf ros2_exercise_basic
```

Your workspace should now look like this:

```text
~/ros2_ws/
└── src/
    ├── run_docker_ros2_mac.sh
    ├── README.md
    ├── <ros2_package_1>/
    └── <ros2_package_2>/
```

---

## 5. Pull the ROS 2 Humble Docker image

```bash
docker pull osrf/ros:humble-desktop-full
```

This step requires an internet connection.

---

## 6. Run the ROS 2 Docker container

Make the Docker script executable:

```bash
chmod +x ~/ros2_ws/src/run_docker_ros2_mac.sh
```

Run the container:

```bash
source ~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

This starts a long-running ROS 2 Humble container with:

* XQuartz graphics support
* CycloneDDS configuration
* Localhost-only ROS 2 discovery
* The workspace mounted at `/root/ros2_ws`

Use the same session name in every terminal so that all nodes run inside the
same container.

---

## 7. Install required system packages

Inside the Docker container, run:

```bash
apt update
apt install -y \
  python3-pip \
  libxcb-cursor0 \
  ros-humble-rmw-cyclonedds-cpp
```

`python3-pip` is needed to install Python dependencies from
`requirements.txt`.

`libxcb-cursor0` is needed by PyQt6/Qt to load the `xcb` platform plugin.

`ros-humble-rmw-cyclonedds-cpp` provides CycloneDDS, which avoids the DDS
discovery problem encountered with the default middleware under Colima.

This step requires an internet connection.

---

## 8. Configure ROS 2 and CycloneDDS

Inside the container, add the environment configuration to `~/.bashrc`:

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

Exit and reopen the container:

```bash
exit
source ~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

Verify the configuration:

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

---

## 9. Install Python dependencies

If a package has a `requirements.txt`, install it with `pip`.

For example:

```bash
cd ~/ros2_ws/src/goal_point_publisher
python3 -m pip install -r requirements.txt
```

This step requires an internet connection.

---

## 10. Install ROS dependencies and build the workspace

Inside the container:

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
```

If `rosdep update` fails because rosdep has not been initialized, run:

```bash
rosdep init
rosdep update
```

Then run:

```bash
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
```

The `rosdep update` and `rosdep install` steps require an internet connection.

The `colcon build` step does not require internet if all dependencies are
already installed.

---

## 11. Test ROS 2 communication

In the first macOS terminal:

```bash
source ~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

Inside the container:

```bash
ros2 run demo_nodes_cpp talker
```

Open another macOS terminal and enter the same container:

```bash
source ~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

Inside the container:

```bash
ros2 topic list --no-daemon
ros2 run demo_nodes_py listener
```

The topic list should include `/chatter`, and the listener should receive
messages from the talker.

---

## 12. Test graphics

Make sure XQuartz is running on macOS:

```bash
open -a XQuartz
xhost +localhost
xhost +127.0.0.1
```

Enter the container:

```bash
source ~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

Run turtlesim:

```bash
ros2 run turtlesim turtlesim_node
```

The turtlesim window should appear through XQuartz.

RViz can be tested with:

```bash
rviz2
```

RViz uses software rendering in this setup and may run more slowly than it does
on native Linux.

---

## 13. Run the exercise

Enter the container:

```bash
source ~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

Inside the container:

```bash
cd ~/ros2_ws
source install/setup.bash
ros2 launch turtlesim_controller go_to_goal.launch.py
```

This should open:

* The turtlesim simulator GUI
* The goal publisher interface GUI
* The robot position-controller node

---

## 14. Daily workflow

Start XQuartz and allow local connections:

```bash
open -a XQuartz
xhost +localhost
xhost +127.0.0.1
```

Start Colima:

```bash
colima start
```

Open the ROS 2 container:

```bash
source ~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

For every additional terminal, run the same command with the same session name:

```bash
source ~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

---

## 15. Notes about the Docker script

The script:

```bash
run_docker_ros2_mac.sh
```

starts a Docker container with:

* ROS 2 Humble Desktop Full
* XQuartz graphics support
* CycloneDDS
* `ROS_LOCALHOST_ONLY=1`
* Qt shared-memory compatibility settings
* Software OpenGL rendering
* The workspace mounted from `~/ros2_ws` to `/root/ros2_ws`

The container name is passed as an argument:

```bash
source ~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

To create or enter a different container session:

```bash
source ~/ros2_ws/src/run_docker_ros2_mac.sh session2
```

For normal use, use the same session name in every terminal:

```bash
source ~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

If the container is already running, the script opens a new shell inside the
same container. Do not create a separate container for each ROS 2 node.

---

## 16. Stop the environment

Exit each container terminal:

```bash
exit
```

Stop the container:

```bash
docker stop session1
```

Stop Colima when it is no longer needed:

```bash
colima stop
```

The workspace remains stored at:

```text
~/ros2_ws
```
