#!/usr/bin/env bash

CONTAINER_NAME="${1:-ros2_humble_gui}"
IMAGE_NAME="osrf/ros:humble-desktop"
WORKSPACE="$HOME/ros2_ws"

mkdir -p "$WORKSPACE"

if ! colima status >/dev/null 2>&1; then
    echo "Colima is not running. Start it with:"
    echo "  colima start"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "Docker is not available. Check Colima with:"
    echo "  colima status"
    exit 1
fi

if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
    if docker ps --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
        echo "Container is already running. Opening a new shell..."
        docker exec -it "$CONTAINER_NAME" bash -lc "
            source /opt/ros/humble/setup.bash
            if [ -f /root/ros2_ws/install/setup.bash ]; then
                source /root/ros2_ws/install/setup.bash
            fi
            cd /root/ros2_ws
            exec bash
        "
    else
        echo "Container exists but is stopped. Starting and attaching..."
        docker start -ai "$CONTAINER_NAME"
    fi
else
    echo "Container does not exist. Creating it..."
    docker run -it \
      --name "$CONTAINER_NAME" \
      --network host \
      --ipc host \
      -e DISPLAY=host.docker.internal:0 \
      -e QT_QPA_PLATFORM=xcb \
      -e ROS_DOMAIN_ID=0 \
      -v "$WORKSPACE":/root/ros2_ws \
      "$IMAGE_NAME"
fi
