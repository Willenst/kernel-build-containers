#!/bin/bash
# Warm Docker/Podman build caches before running tests.
#
# Idea:
#
# The normal image manager removes final images with `rmi`. For Podman this
# would remove untagged intermediate layers, so subsequent builds lose their
# local layer cache. This script builds every supported toolchain once, labels
# its intermediate layers, and adds tags to them. The temporary warmup
# image is removed afterwards; only the reusable cache layers remain.
#
# Docker keeps its builder cache independently, so its part simply builds all
# images once and removes the final images afterwards.

set -e

MIN_SPACE_GB=100    # Aproximate size of all containers combined
cleanup=false
force=false
podman=false
docker=false

usage() {
    echo "Usage: $0 [--podman] [--docker] [--cleanup] [--force]"
    echo
    echo "  --podman   warm or clean Podman cache only"
    echo "  --docker   warm Docker cache only"
    echo "  --cleanup  remove Podman cache layers"
    echo "  --force    skip free-space check"
}

for arg in "$@"; do
    case "$arg" in
        --cleanup) cleanup=true ;;
        --force) force=true ;;
        --podman) podman=true ;;
        --docker) docker=true ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            usage
            exit 1
            ;;
    esac
done

if ! $podman && ! $docker; then
    podman=true
    docker=true
fi

compilers=(
    "5 4.9 16.04"
    "6 5 16.04"
    "7 6 18.04"
    "8 7 18.04"
    "9 8 20.04"
    "10 9 20.04"
    "11 10 20.04"
    "12 11 22.04"
    "13 12 22.04"
    "14 12 22.04"
    "15 13 24.04"
    "16 14 24.04"
    "17 14 24.04"
    "18 14 24.04"
    "19 15 26.04"
    "20 15 26.04"
    "21 16 26.04"
    "22 16 26.04"
)

if $cleanup; then
    if $podman; then
        echo "Removing Podman cache..."

        for c in "${compilers[@]}"; do
            read clang gcc ubuntu <<< "$c"

            for id in $(podman image ls -aq \
                --filter "label=kernel-build-cache=gcc-$gcc-clang-$clang"); do
                podman rmi -f "$id" 2>/dev/null || true
            done
        done
    fi

    exit 0
fi


if ! $force; then
    free_kb=$(df -Pk "$HOME" | awk 'END { print $4 }')
    required_kb=$((MIN_SPACE_GB * 1024 * 1024))
    free_gb=$((free_kb / 1024 / 1024))

    if ((free_kb < required_kb)); then
        echo "Free space is ${free_gb} GiB"
        echo "Must be at least $MIN_SPACE_GB GiB"
        echo "Use '$0 --force' to ignore this check."
        exit 1
    fi
fi

if $podman; then
    echo "Warming Podman cache..."

    for c in "${compilers[@]}"; do
        read clang gcc ubuntu <<< "$c"

        name="gcc-$gcc-clang-$clang"
        warmup="kernel-build-warmup:$name"

        echo "  clang-$clang / gcc-$gcc / Ubuntu $ubuntu"

        podman build \
            --layers \
            --layer-label "kernel-build-cache=$name" \
            --build-arg CLANG_VERSION="$clang" \
            --build-arg GCC_VERSION="$gcc" \
            --build-arg UBUNTU_VERSION="$ubuntu" \
            --build-arg UNAME="$(whoami)" \
            --build-arg GNAME="$(id -gn)" \
            --build-arg UID="$(id -u)" \
            --build-arg GID="$(id -g)" \
            -t "$warmup" \
            .

        for id in $(podman image ls -aq \
            --filter "label=kernel-build-cache=$name"); do
            podman tag "$id" "kernel-build-cache:$name-$id"
        done

        podman rmi -f "$warmup"
    done
fi

if $docker; then
    if command -v docker >/dev/null 2>&1; then
        echo "Warming Docker cache..."
        python3 manage_images.py -d -b all
        python3 manage_images.py -d -r all
    else
        echo "Docker is not installed; skipping Docker cache."
    fi
fi

echo "Cache baked."
echo
echo "WARNING: the warmed caches can use substantial disk space."
echo "If you do not need other local containers, images, volumes, or build cache,"
echo "remove everything with:"
echo "  podman system prune -a --volumes"
echo "  docker system prune -a --volumes"
