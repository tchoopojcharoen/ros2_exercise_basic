#!/usr/bin/env bash

# Open a persistent ROS 2 Humble development container on macOS with Colima.

main() {
    local container_name="${1:-}"
    local image="osrf/ros:humble-desktop-full"
    local workspace="${HOME}/ros2_ws"

    if [[ -z "${container_name}" ]]; then
        echo "Usage: source $BASH_SOURCE <session_name>"
        echo "Example: source $BASH_SOURCE session1"
        return 1
    fi

    if ! command -v docker >/dev/null 2>&1; then
        echo "Error: docker was not found. Install Docker CLI and start Colima."
        return 1
    fi

    if ! docker info >/dev/null 2>&1; then
        echo "Error: Docker is not running."
        echo "Start Colima with: colima start"
        return 1
    fi

    mkdir -p "${workspace}/src" || return 1

    if ! docker image inspect "${image}" >/dev/null 2>&1; then
        echo "Docker image ${image} is not available."
        echo "Pull it with: docker pull ${image}"
        return 1
    fi

    if ! docker container inspect "${container_name}" >/dev/null 2>&1; then
        echo "Creating container: ${container_name}"

        docker run -dit \
            --name "${container_name}" \
            --hostname "${container_name}" \
            --privileged \
            --shm-size=2g \
            -e DISPLAY=host.docker.internal:0 \
            -e QT_X11_NO_MITSHM=1 \
            -e LIBGL_ALWAYS_SOFTWARE=1 \
            -e ROS_DOMAIN_ID=0 \
            -e ROS_LOCALHOST_ONLY=1 \
            -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
            -v "${workspace}:/root/ros2_ws" \
            -w /root/ros2_ws \
            "${image}" \
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
        -e DISPLAY=host.docker.internal:0 \
        -e QT_X11_NO_MITSHM=1 \
        -e LIBGL_ALWAYS_SOFTWARE=1 \
        -e ROS_DOMAIN_ID=0 \
        -e ROS_LOCALHOST_ONLY=1 \
        -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
        -w /root/ros2_ws \
        "${container_name}" \
        bash
}

main "$@"
