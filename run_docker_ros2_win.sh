#!/usr/bin/env bash

# Open one persistent ROS 2 Humble development container under Windows/WSL.

main() {
    local container_name="${1:-session1}"
    local image_name="osrf/ros:humble-desktop"
    local workspace="${HOME}/ros2_ws"

    if ! command -v docker >/dev/null 2>&1; then
        echo "Error: docker was not found inside WSL."
        echo "Start Docker Desktop and enable integration for this WSL distribution."
        return 1
    fi

    if ! docker info >/dev/null 2>&1; then
        echo "Error: Docker is not running or is not available inside WSL."
        echo "Start Docker Desktop, then try again."
        return 1
    fi

    mkdir -p "${workspace}/src" || return 1

    if ! docker image inspect "${image_name}" >/dev/null 2>&1; then
        echo "Docker image ${image_name} is not available."
        echo "Pull it with: docker pull ${image_name}"
        return 1
    fi

    if ! docker container inspect "${container_name}" >/dev/null 2>&1; then
        echo "Creating container: ${container_name}"

        docker run -dit \
            --name "${container_name}" \
            --hostname "${container_name}" \
            --network host \
            --ipc host \
            --shm-size=2g \
            -e DISPLAY="${DISPLAY:-:0}" \
            -e WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}" \
            -e XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/mnt/wslg/runtime-dir}" \
            -e PULSE_SERVER="${PULSE_SERVER:-/mnt/wslg/PulseServer}" \
            -e QT_QPA_PLATFORM=xcb \
            -e ROS_DOMAIN_ID=0 \
            -v /tmp/.X11-unix:/tmp/.X11-unix \
            -v /mnt/wslg:/mnt/wslg \
            -v "${workspace}:/root/ros2_ws" \
            -w /root/ros2_ws \
            "${image_name}" \
            bash

        if [[ $? -ne 0 ]]; then
            echo "Error: failed to create container ${container_name}."
            return 1
        fi
    elif [[ "$(docker inspect -f '{{.State.Running}}' "${container_name}")" != "true" ]]; then
        echo "Starting container: ${container_name}"
        docker start "${container_name}" >/dev/null || return 1
    fi

    echo "Opening ROS 2 shell in container: ${container_name}"

    docker exec -it \
        -e DISPLAY="${DISPLAY:-:0}" \
        -e WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}" \
        -e XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/mnt/wslg/runtime-dir}" \
        -e PULSE_SERVER="${PULSE_SERVER:-/mnt/wslg/PulseServer}" \
        -e QT_QPA_PLATFORM=xcb \
        -e ROS_DOMAIN_ID=0 \
        -w /root/ros2_ws \
        "${container_name}" \
        bash -lc '
            source /opt/ros/humble/setup.bash
            if [ -f /root/ros2_ws/install/setup.bash ]; then
                source /root/ros2_ws/install/setup.bash
            fi
            exec bash
        '
}

main "$@"
