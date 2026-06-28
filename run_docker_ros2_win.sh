#!/usr/bin/env bash

CONTAINER_NAME="${1:-ros2_humble_gui}"
IMAGE_NAME="osrf/ros:humble-desktop"
WORKSPACE="$HOME/ros2_ws"

mkdir -p "$WORKSPACE"

if ! docker info >/dev/null 2>&1; then
    echo "Docker is not running or not available."
    echo "Check your Docker installation, then try again."
    exit 1
fi

if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
    if docker ps --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
        docker exec -it "$CONTAINER_NAME" bash -lc "
            source /opt/ros/humble/setup.bash
            if [ -f /root/ros2_ws/install/setup.bash ]; then
                source /root/ros2_ws/install/setup.bash
            fi
            cd /root/ros2_ws
            exec bash
        "
    else
        docker start -ai "$CONTAINER_NAME"
    fi
else
    docker run -it \
      --name "$CONTAINER_NAME" \
      --network host \
      --ipc host \
      -e DISPLAY="$DISPLAY" \
      -e WAYLAND_DISPLAY="$WAYLAND_DISPLAY" \
      -e XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
      -e QT_QPA_PLATFORM=xcb \
      -e ROS_DOMAIN_ID=0 \
      -v /tmp/.X11-unix:/tmp/.X11-unix \
      -v /mnt/wslg:/mnt/wslg \
      -v "$WORKSPACE":/root/ros2_ws \
      "$IMAGE_NAME"
fi
