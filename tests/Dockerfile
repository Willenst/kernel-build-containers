FROM busybox:1.36.1

ARG CLANG_VERSION
ARG GCC_VERSION
ARG UBUNTU_VERSION
ARG UNAME
ARG GNAME
ARG UID
ARG GID

# Different build args are needed for different image IDs
RUN printf '%s\n' \
        "clang=${CLANG_VERSION}" \
        "gcc=${GCC_VERSION}" \
        "ubuntu=${UBUNTU_VERSION}" \
        "user=${UNAME}" \
        "group=${GNAME}" \
        "uid=${UID}" \
        "gid=${GID}" \
        > build-id.txt