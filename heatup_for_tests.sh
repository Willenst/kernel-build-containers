#!/bin/bash
# Heat up caches before running tests

CLEANUP=false
MIN_SPACE_GB=100 # Aproximate size of all containers for docker and podman

set -e

if [ "${1:-}" = "--cleanup" ]; then
    CLEANUP=true
elif [ -n "${1:-}" ]; then
    echo "Usage: $0 [--cleanup]"
    exit 1
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

if $CLEANUP; then
    echo 'remove dummy Podman images and cache layers'

    for c in "${compilers[@]}"; do
        read clang gcc ubuntu <<< "$c"

        podman rmi -f "dummy:$gcc-$clang" 2>/dev/null || true

        for id in $(podman image ls -a \
            --filter "label=dummylabel=$gcc-$clang" \
            --format '{{.ID}}'); do
            podman rmi -f "$id" 2>/dev/null || true
        done
    done

    exit 0
fi

echo 'prepare dummy Podman images for faster test runs'

for c in "${compilers[@]}"; do
    read clang gcc ubuntu <<< "$c"

    echo "Building clang-$clang / gcc-$gcc on Ubuntu $ubuntu"

    podman build \
        --layers \
        --label "dummylabel-final=$gcc-$clang" \
        --layer-label "dummylabel=$gcc-$clang" \
        --build-arg CLANG_VERSION="$clang" \
        --build-arg GCC_VERSION="$gcc" \
        --build-arg UBUNTU_VERSION="$ubuntu" \
        --build-arg UNAME="$(whoami)" \
        --build-arg GNAME="$(id -gn)" \
        --build-arg UID="$(id -u)" \
        --build-arg GID="$(id -g)" \
        -t "dummy:$gcc-$clang" \
        .
    
    for id in $(podman image ls -a \
        --filter "label=dummylabel=$gcc-$clang" \
        --format '{{.ID}}'); do
        podman tag "$id" "dummylabel:$gcc-$clang-$id"
    done
done

if command -v docker >/dev/null 2>&1; then
    echo
    echo 'prepare Docker build cache'

    #python3 manage_images.py -d -b all

    echo
    echo 'remove Docker images, keep Docker build cache'

    #python3 manage_images.py -d -r all
else
    echo
    echo 'Docker is not installed, skip Docker build cache'
fi

echo
echo "Cache baked."
echo "Podman final images: dummy:*"
echo "Podman cache layers: dummylabel:*"
echo "To remove Podman cache: $0 --cleanup"