# Appendix: Running RViz2 on macOS

This appendix extends [SETUP_MAC.md](https://github.com/tchoopojcharoen/ros2_exercise_basic/blob/main/SETUP_MAC.md). The main tutorial gets ROS 2 GUI apps such as `turtlesim` on screen through XQuartz. RViz2 is heavier: it needs OpenGL/3D acceleration that XQuartz forwards poorly under Colima, so RViz2 often crashes, renders black, or complains about GLX.

The reliable workaround is to **not** forward RViz2 to XQuartz at all. Instead we run a small virtual desktop *inside* the container (a headless X display + a window manager + a VNC server) and view it from the Mac in a normal web browser through noVNC. RViz2 renders with software OpenGL inside the container, and only the resulting picture is streamed to the browser.

This appendix assumes you have already completed the full **One-Time Mac Setup** and **One-Time Container Setup** from `SETUP_MAC.md`.

## Setup (do this before running the daily commands)

### A. Publish the noVNC port in the Docker launch script

The virtual desktop is served on port `6080` inside the container. To reach it from the Mac browser, the container must publish that port, so it has to be added to the `docker run` command in the launch script.

Open the script:

```bash
nano ~/ros2_ws/src/run_docker_ros2_mac.sh
```

Find the `docker run` command and add these two lines alongside the other `-p` / flag lines (keep the trailing backslashes so the command stays on one logical line):

```bash
-p 6080:6080 \
--dns 8.8.8.8 \
```

* `-p 6080:6080` maps container port 6080 (noVNC) to `localhost:6080` on the Mac.
* `--dns 8.8.8.8` gives the container a reliable DNS server, which avoids `apt` failing to resolve package mirrors on some networks. It is optional but recommended.

Save and exit nano (`Ctrl+O`, `Enter`, then `Ctrl+X`).

> **Important:** published ports are fixed when the container is created. If your `session1` container already exists, the new `-p` flag will not apply to it. Remove the old container and recreate it so the port takes effect:
>
> ```bash
> docker rm -f session1   # run on the Mac, not inside the container
> ```
>
> Then re-enter it with the command in step 2 below, which recreates it using the updated script. (Recreating means the packages in step 3 must be installed again.)

### B. What you need before starting

* The base `SETUP_MAC.md` setup finished (Colima, Docker, the `~/ros2_ws` workspace, and the `run_docker_ros2_mac.sh` script).
* The port-mapping edit above applied and the container (re)created from the updated script.
* An internet connection the first time, to install the virtual-desktop packages in step 3.

Once the container is created with port 6080 published, the GUI packages (step 3) persist across stop/restart, so on later days you only repeat steps 1, 2, 4, 5 and 6.

## Daily workflow for RViz2

### 1. Start XQuartz and Colima on the Mac

```bash
open -a XQuartz
```

Launches the XQuartz X11 server on macOS.

```bash
export DISPLAY=:0
/opt/X11/bin/xhost +localhost
/opt/X11/bin/xhost +127.0.0.1
```

Points the shell at the XQuartz display and authorizes clients from `localhost` and the `127.0.0.1` loopback address to connect to it.

```bash
colima start
```

Starts the Colima virtual machine that runs the Docker engine (reports "already running" if it is up).

### 2. Enter the container

```bash
source ~/ros2_ws/src/run_docker_ros2_mac.sh session1
```

Starts (or creates) the named `session1` container with port 6080 published and opens a shell inside it.

### 3. Install the virtual-desktop packages (first time per container only)

```bash
apt-get update && apt-get install -y xvfb x11vnc fluxbox novnc websockify ros-humble-rmw-cyclonedds-cpp
```

Installs the headless X server (`xvfb`), VNC server (`x11vnc`), lightweight window manager (`fluxbox`), the browser-based VNC client (`novnc`) and its bridge (`websockify`), plus the CycloneDDS middleware.

### 4. Start the virtual desktop and noVNC bridge

```bash
Xvfb :1 -screen 0 1280x1024x24 &
export DISPLAY=:1
fluxbox &
x11vnc -display :1 -nopw -forever -bg
websockify --web /usr/share/novnc 6080 localhost:5900 &
```

Line by line:

* `Xvfb :1 -screen 0 1280x1024x24 &` — creates a virtual (off-screen) X display `:1` at 1280×1024 for GUI apps to draw into.
* `export DISPLAY=:1` — tells GUI programs in this shell to render to that virtual display.
* `fluxbox &` — starts a minimal window manager so RViz2 windows can be moved and resized.
* `x11vnc -display :1 -nopw -forever -bg` — shares display `:1` over VNC with no password, staying alive across client disconnects, in the background.
* `websockify --web /usr/share/novnc 6080 localhost:5900 &` — bridges the VNC server (port 5900) to the noVNC web client on port 6080.

### 5. Source ROS 2 and point it at the virtual display

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
export DISPLAY=:1
export CYCLONEDDS_URI='<CycloneDDS><Domain id="any"><General><AllowMulticast>false</AllowMulticast></General><Discovery><ParticipantIndex>auto</ParticipantIndex><MaxAutoParticipantIndex>1000</MaxAutoParticipantIndex></Discovery></Domain></CycloneDDS>'
```

You can now launch RViz2 in this terminal (`rviz2`) and it will appear in the virtual desktop.

### 6. Open the desktop in your Mac browser

```
http://localhost:6080/vnc.html
```

Open this URL in any browser on the Mac to view the container's virtual desktop — and RViz2 — through noVNC.

### 7. (Optional) Direct XQuartz method instead of noVNC

```bash
export DISPLAY=192.168.5.2:0
ros2 run turtlesim turtlesim_node
```

Points the container at the Mac's XQuartz over the Colima network gateway IP (`192.168.5.2`) and launches a GUI node directly. This is a lightweight alternative that works for `turtlesim`, but is not reliable for RViz2 — use the noVNC method above for RViz2.

---

## Cleanup / restarting the desktop

If the virtual desktop misbehaves or you want to restart it, stop the processes and clear the stale display files before starting again.

```bash
pkill -f Xvfb
pkill -f x11vnc
pkill -f fluxbox
pkill -f websockify
```

Stops the virtual X server, VNC server, window manager and noVNC bridge.

```bash
rm -rf /tmp/.X11-unix/X1
rm -rf /tmp/.X*lock
```

Removes the leftover X11 socket and lock files for display `:1` so it can be started cleanly again (repeat step 4 afterwards).

---

## Troubleshooting

* **Browser shows "unable to connect" on port 6080** — the container was created before the `-p 6080:6080` edit. Recreate it (see Setup step A) or confirm `docker ps` lists `0.0.0.0:6080->6080/tcp`.
* **`Xvfb` fails: server already active for display 1** — a previous session left display `:1` running; run the cleanup commands above, then retry step 4.
* **RViz2 window is black or crashes** — make sure `DISPLAY=:1` is set in the *same* terminal that launches `rviz2`; software rendering may also need `export LIBGL_ALWAYS_SOFTWARE=1` before starting RViz2.
* **noVNC connects but the desktop is empty** — that is normal until you launch a GUI app; run `rviz2` (or `fluxbox`'s right-click menu) to open something.
