# ROS 2 Basic Exercise

This repository contains basic ROS 2 packages and a helper script for running ROS 2 Humble inside Docker on Windows/WSL.

The setup assumes:

* Windows with WSL installed
* Docker works from inside WSL
* The Docker image used is `osrf/ros:humble-desktop`
* A ROS 2 workspace is located at `~/ros2_ws`

---

## Internet Connection Requirement

An internet connection is required when:

* Cloning this repository
* Pulling the Docker image
* Installing Linux packages with `apt`
* Installing Python packages with `pip`
* Installing ROS dependencies with `rosdep`

After all required packages are installed and the workspace has been built, an internet connection is **not required** to run existing ROS 2 nodes or launch files locally.

---

## 1. Open WSL

Open PowerShell and run:

```powershell
wsl
```

---

## 2. Create a ROS 2 workspace

Inside WSL:

```bash
cd ~
mkdir -p ~/ros2_ws/src
```

---

## 3. Clone this repository

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
    ├── run_docker_ros2_win.sh
    ├── README.md
    ├── <ros2_package_1>/
    └── <ros2_package_2>/
```

---

## 4. Pull the ROS 2 Humble Docker image

Before running the Docker script, pull the ROS 2 Humble desktop image:

```bash
docker pull osrf/ros:humble-desktop
```

This step requires an internet connection.

---

## 5. Run the ROS 2 Docker container

Make the Docker script executable:

```bash
chmod +x ~/ros2_ws/src/run_docker_ros2_win.sh
```

Run the container:

```bash
source ~/ros2_ws/src/run_docker_ros2_win.sh session1
```

This starts a ROS 2 Humble Docker container with graphics and networking enabled.

---

## 6. Install required system packages inside the container

Inside the Docker container, run:

```bash
apt update
apt install -y python3-pip libxcb-cursor0
```

`python3-pip` is needed to install Python dependencies from `requirements.txt`.

`libxcb-cursor0` is needed by PyQt6/Qt to load the `xcb` platform plugin. Without it, you may see an error like:

```text
qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin.
```

This step requires an internet connection.

---

## 7. Install Python dependencies

If a package has a `requirements.txt`, install it with `pip`.

For example:

```bash
cd ~/ros2_ws/src/goal_point_publisher
python3 -m pip install -r ~/ros2_ws/src/goal_point_publisher/requirements.txt
```

This step requires an internet connection.

---

## 8. Install ROS dependencies and build the workspace (This is for main branch main only)

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

The `colcon build` step does not require internet if all dependencies are already installed.

---

## 9. Run an example (Not available from tutorial branch)

After building, source the workspace:

```bash
ros2 launch turtlesim_controller go_to_goal.launch.py
```
This should run a turtlesim simualtor GUI, a goal publisher interface GUI, and the back-end position-controller of the robot. 

---

## 12. Notes about the Docker script

The script:

```bash
run_docker_ros2_win.sh
```

starts a Docker container with:

* ROS 2 Humble
* WSL graphics support
* Host networking
* Shared IPC
* The workspace mounted from `~/ros2_ws` to `/root/ros2_ws`

The container name is passed as an argument:

```bash
~/ros2_ws/src/run_docker_ros2_win.sh session1
```

To create or enter a different container session:

```bash
~/ros2_ws/src/run_docker_ros2_win.sh session2
```

For normal use, use the same session name in every terminal:

```bash
~/ros2_ws/src/run_docker_ros2_win.sh session1
```

If the container is already running, the script opens a new shell into the same container.
