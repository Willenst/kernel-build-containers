#!/usr/bin/python3

"""
This module provides functionality to manage Docker containers
that are configured for building kernels with specific versions
of GCC and Clang compilers.
"""

import os
import subprocess
import sys
import argparse
from typing import List, Optional

class Container:
    """
    Represents a Docker container configured for kernel building.

    Attributes:
        gcc (str): Version of GCC compiler.
        clang (str): Version of Clang compiler (optional).
        ubuntu (str): Version of Ubuntu.
        tag (str): Docker image tag.
        is_alive (bool): Whether the container is built.
    """
    def __init__(self, gcc_version: str, clang_version: Optional[str], ubuntu_version: str) -> None:
        self.gcc = gcc_version
        self.clang = clang_version
        self.ubuntu = ubuntu_version
        self.tag: Optional[str] = None
        self.is_alive = self.live_check()

    def add(self) -> None:
        """Builds the Docker container with the specified compiler"""
        build_args=['--build-arg', f'GCC_VERSION={self.gcc}',
                    '--build-arg', f'UBUNTU_VERSION={self.ubuntu}',
                    '--build-arg', f'UNAME={os.getlogin()}',
                    '--build-arg', f'UID={os.getuid()}',
                    '--build-arg', f'GID={os.getgid()}'
        ]
        if self.clang:
            subprocess.run([SUDO_CMD, 'docker', 'build', '--build-arg',
                            f'CLANG_VERSION={self.clang}', *build_args,
                            '-t', f'kernel-build-container:clang-{self.clang}_gcc-{self.gcc}', '.'],
                           text=True, check=True)
            self.live_check()
        else:
            subprocess.run([SUDO_CMD, 'docker', 'build', *build_args,
                            '-t', f'kernel-build-container:gcc-{self.gcc}', '.'],
                           text=True, check=True)
            self.live_check()

    def rm(self) -> None:
        """Removes the Docker container if it exists"""
        if self.tag:
            subprocess.run([SUDO_CMD, 'docker', 'rmi',
                            f'kernel-build-container:{self.tag}'],
                            text=True, check=True)
            self.live_check()
        else:
            print('No such container')

    def live_check(self) -> bool:
        """Checks if the Docker container with the specified tag exists"""
        if self.gcc:
            compiler = f'gcc-{self.gcc}'
            if self.clang:
                compiler = f'clang-{self.clang}'
            cmd = subprocess.run([SUDO_CMD, 'docker', 'images', '--format', '{{.Tag}}'],
                                 stdout=subprocess.PIPE,
                                 text=True, check=True)
            container_tags=cmd.stdout.strip().split()
            for tag in container_tags:
                if compiler in tag:
                    self.tag = tag
                    return True
        self.tag = None
        return False

def extract_containers() -> List[str]:
    """Extracts the list of existing container tags from Docker"""
    containers = subprocess.run([SUDO_CMD, 'docker', 'images', '--format', '{{.Tag}}'],
                                stdout=subprocess.PIPE,
                                text=True, check=True)
    compilers=containers.stdout.strip().split()
    return compilers

def check_group() -> str:
    """Checks if the user is in the Docker group, returns 'sudo' if not"""
    result = subprocess.run(['groups'], capture_output=True,
                            text=True, check=True)
    if 'docker' in result.stdout:
        return ''
    print("Hey, we gonna use sudo for running docker")
    return 'sudo'

def add_handler(needed_compiler: str, containers: List[Container]) -> None:
    """Adds the specified container(s) based on the provided compiler"""
    if needed_compiler == 'all':
        for c in containers:
            if not c.is_alive:
                print(f'Adding container for {needed_compiler} '
                      f'on {c.ubuntu} with gcc {c.gcc} and clang {c.clang}')
                c.add()
        return
    for c in containers:
        if 'gcc-' + c.gcc == needed_compiler:
            if c.is_alive:
                sys.exit(f'[!] ERROR: container with the compiler'
                         f'{needed_compiler} already exists!')
            print(f'Adding container for {needed_compiler} '
                  f'on {c.ubuntu} with gcc {c.gcc} and clang {c.clang}')
            c.add()
            return
        if c.clang and 'clang-' + c.clang == needed_compiler:
            if c.is_alive:
                sys.exit(f'[!] ERROR: container with the compiler'
                         f'{needed_compiler} already exists!')
            print(f'Adding container for {needed_compiler} '
                  f'on {c.ubuntu} with gcc {c.gcc} and clang {c.clang}')
            c.add()
            return
    sys.exit('[!] ERROR: no container with the compiler "{needed_compiler}"')

def remove_handler(removed_compiler: str, containers: List[Container]) -> None:
    """Removes the specified container(s) based on the provided compiler"""
    if removed_compiler == 'all':
        for c in containers:
            if c.is_alive:
                print(f'Removing container for {removed_compiler} '
                      f'on {c.ubuntu} with gcc {c.gcc} and clang {c.clang}')
                c.rm()
        return
    for c in containers:
        if 'gcc-' + c.gcc == removed_compiler:
            print(f'Removing container for {removed_compiler} '
                  f'on {c.ubuntu} with gcc {c.gcc} and clang {c.clang}')
            c.rm()
            return
        if c.clang and 'clang-' + c.clang == removed_compiler:
            print(f'Removing container for {removed_compiler} '
                  f'on {c.ubuntu} with gcc {c.gcc} and clang {c.clang}')
            c.rm()
            return
    sys.exit('[!] ERROR: no container with the compiler "{needed_compiler}"')

def main() -> None:
    """Main function to manage the containers"""
    containers = []
    containers += [Container("4.9", None, "16.04")]
    containers += [Container("5", None, "16.04")]
    containers += [Container("6", None, "18.04")]
    containers += [Container("7", None, "18.04")]
    containers += [Container("8", None, "20.04")]
    containers += [Container("9", None, "20.04")]
    containers += [Container("10", None, "20.04")]
    containers += [Container("11", "12", "22.04")]
    containers += [Container("12", "13", "22.04")]
    containers += [Container("12", "14", "22.04")]
    containers += [Container("13", "15", "23.04")]
    containers += [Container("14", "16", "24.04")]
    containers += [Container("14", "17", "24.04")]

    compilers = ['gcc-4.9',
                 'gcc-5',
                 'gcc-6',
                 'gcc-7',
                 'gcc-8',
                 'gcc-9',
                 'gcc-10',
                 'gcc-11',
                 'gcc-12',
                 'gcc-13',
                 'gcc-14',
                 'clang-12',
                 'clang-13',
                 'clang-14',
                 'clang-15',
                 'clang-16',
                 'clang-17',
                 'all']

    parser = argparse.ArgumentParser(description='Manage the kernel-build-containers')
    parser.add_argument('-l','--list', action='store_true',
                        help='show the kernel build containers')
    parser.add_argument('-a','--add', choices=compilers, nargs='+',
                        help='build a container with this compiler (\'all\' to build all of them)')
    parser.add_argument('-r','--remove', choices=compilers, nargs='+',
                    help='remove a container with this compiler (\'all\' to remove all of them)')
    args = parser.parse_args()

    if args.list:
        for c in containers:
            if c.is_alive:
                status = '[+]'
            else:
                status = '[-]'
            print(f'container with gcc {c.gcc} and clang {c.clang} on ubuntu {c.ubuntu}: {status}')
        sys.exit(0)

    if args.add:
        for compiler in args.add:
            add_handler(compiler,containers)
    elif args.remove:
        for compiler in args.remove:
            remove_handler(compiler,containers)
    else:
        parser.print_help()
        sys.exit(0)

SUDO_CMD = check_group()
if __name__ == '__main__':
    main()
