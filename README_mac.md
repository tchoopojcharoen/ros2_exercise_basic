# ROS 2 Basic Exercise on macOS with Colima

This guide explains how to run the ROS 2 Humble exercises on macOS using:

* Colima
* Docker CLI
* XQuartz for GUI windows
* The Docker image `osrf/ros:humble-desktop`

This setup assumes that Colima and Docker are already installed.

---

## Internet Connection Requirement

An internet connection is required when:

* Cloning this repository
* Pulling the Docker image
* Installing Linux packages with `apt`
* Installing Python packages with `pip`
* Installing ROS dependencies with `rosdep`

After the required packages are installed and the workspace has been built, an internet connection is not required to run existing ROS 2 nodes or launch files locally.

---

## 1. Start Colima

```bash
colima start
docker ps
```

If `docker ps` runs without error, Docker is ready.

---

## 2. Install and Configure XQuartz for GUI Applications

XQuartz is needed for GUI applications such as `turtlesim` and PyQt6 GUI nodes.

```bash
brew install --cask xquartz
defaults write org.xquartz.X11 nolisten_tcp -bool false
xhost +localhost
xhost + 127.0.0.1
```

---

## 3. Create a ROS 2 Workspace

```bash
cd ~
mkdir -p ~/ros2_ws/src
```

The workspace is:

```text
~/ros2_ws
```

The source folder is:

```text
~/ros2_ws/src
```

---

## 4. Clone This Repository

```bash
cd ~
git clone -b main https://github.com/tchoopojcharoen/ros2_exercise_basic.git
mv ros2_exercise_basic/* ~/ros2_ws/src/
rm -rf ros2_exercise_basic
```

The workspace should now look like this:

```text
~/ros2_ws/
└── src/
    ├── run_docker_ros2_mac.sh
    ├── README.md
    ├── <ros2_package_1>/
    └── <ros2_package_2>/
```

---

## 5. Pull the ROS 2 Humble Docker Image

```bash
docker pull osrf/ros:humble-desktop
```

---

## 6. Run the ROS 2 Docker Container

Make the Docker script executable:

```bash
chmod +x ~/ros2_ws/src/run_docker_ros2_mac.sh
```

Run the container:

```bash
~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

Inside the container, the workspace is mounted at:

```text
~/ros2_ws
```

So the mapping is:

```text
macOS:     ~/ros2_ws
Container: ~/ros2_ws
```

To open another terminal into the same container, open another macOS Terminal window and run:

```bash
~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

---

## 7. Install Required System Packages Inside the Container

Inside the Docker container:

```bash
apt update
apt install -y python3-pip libxcb-cursor0
```

`python3-pip` is needed to install Python dependencies from `requirements.txt`.

`libxcb-cursor0` is needed by PyQt6/Qt to load the `xcb` platform plugin.

---

## 8. Install Python Dependencies

If a package has a `requirements.txt`, install it with `pip`.

Example:

```bash
cd ~/ros2_ws/src/<package_name>
python3 -m pip install -r requirements.txt
```

For the PyQt6 GUI package, `requirements.txt` should contain:

```text
PyQt6
PyYAML
```

---

## 9. Install ROS Dependencies and Build the Workspace

Inside the container:

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
```

If `rosdep update` fails because rosdep has not been initialized:

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

---


## 10. Run an example

After building, source the workspace:

```bash
ros2 launch turtlesim_controller go_to_goal.launch.py
```
This should run a turtlesim simualtor GUI, a goal publisher interface GUI, and the back-end position-controller of the robot. 

---

## 11. Notes About the Docker Script

The script:

```text
run_docker_ros2_mac.sh
```

starts a Docker container with:

* ROS 2 Humble
* XQuartz graphics support
* Host networking
* Shared IPC
* The workspace mounted from `~/ros2_ws` to `~/ros2_ws`

The container name is passed as an argument:

```bash
~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

To create or enter a different container session:

```bash
~/ros2_ws/src/run_docker_ros2_mac.sh session2
```

For normal use, use the same session name in every terminal:

```bash
~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

If the container is already running, the script opens a new shell into the same container.

---

## 14. Common Issues

### Docker command does not work

Check Colima:

```bash
colima status
```

If it is not running:

```bash
colima start
```

Then test Docker:

```bash
docker ps
```

---

### GUI window does not appear

Run:

```bash
open -a XQuartz
xhost +localhost
xhost + 127.0.0.1
```

Then recreate the container:

```bash
docker rm -f session1
~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

---

### Qt says `xcb-cursor0` or `libxcb-cursor0` is needed

Inside the container:

```bash
apt update
apt install -y libxcb-cursor0
```

Then rerun the node.

---

### Topic appears but `ros2 topic echo` shows no data

Use the same container in multiple terminals:

```bash
~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

Do not create separate containers unless needed.

If separate containers are used, make sure both use:

```text
--network host
--ipc host
```

Also check that all terminals use the same ROS domain:

```bash
echo $ROS_DOMAIN_ID
```

This tutorial uses:

```text
ROS_DOMAIN_ID=0
```
