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

class Container:
    """
    Represents a Docker container configured for kernel building.

    Attributes:
        gcc (str): Version of GCC compiler.
        clang (str): Version of Clang compiler (optional).
        ubuntu (str): Version of Ubuntu.
        tag (str): Docker image tag.
        exists (bool): Whether the container is built.
    """
    def __init__(self, gcc_version, clang_version, ubuntu_version):
        self.gcc = gcc_version
        self.clang = clang_version
        self.ubuntu = ubuntu_version
        self.tag = None
        self.exists = self.check()

    def add(self):
        """Builds the Docker container with the specified compiler"""
        build_args=['--build-arg', f'GCC_VERSION={self.gcc}',
                    '--build-arg', f'UBUNTU_VERSION={self.ubuntu}',
                    '--build-arg', f'UNAME={os.getlogin()}',
                    '--build-arg', f'UID={os.getuid()}',
                    '--build-arg', f'GID={os.getgid()}'
        ]
        if self.clang:
            build_args=['--build-arg', f'CLANG_VERSION={self.clang}']+build_args
        subprocess.run([SUDO_CMD, 'docker', 'build', *build_args,
                        '-t', f'kernel-build-container:gcc-{self.gcc}_clang-{self.clang}', '.'],
                    text=True, check=True)
        self.check()

    def rm(self):
        """Removes the Docker container if it exists"""
        if self.tag:
            subprocess.run([SUDO_CMD, 'docker', 'rmi',
                            f'kernel-build-container:{self.tag}'],
                            text=True, check=True)
            self.check()
        else:
            print('No such container')

    def check(self):
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

def extract_containers():
    """Extracts the list of existing container tags from Docker"""
    containers = subprocess.run([SUDO_CMD, 'docker', 'images', '--format', '{{.Tag}}'],
                                stdout=subprocess.PIPE,
                                text=True, check=True)
    compilers=containers.stdout.strip().split()
    return compilers

def check_group():
    """Checks if the user is in the Docker group, returns 'sudo' if not"""
    result = subprocess.run(['groups'], capture_output=True,
                            text=True, check=True)
    if 'docker' in result.stdout:
        return ''
    print("Hey, we gonna use sudo for running docker")
    return 'sudo'

def add_handler(needed_compiler, containers):
    """Adds the specified container(s) based on the provided compiler"""
    if needed_compiler == 'all':
        for c in containers:
            if not c.exists:
                print(f'Adding container for {needed_compiler} '
                      f'on {c.ubuntu} with gcc {c.gcc} and clang {c.clang}')
                c.add()
        return
    for c in containers:
        if 'gcc-' + c.gcc == needed_compiler:
            if c.exists:
                sys.exit(f'[!] ERROR: container with the compiler'
                         f'{needed_compiler} already exists!')
            print(f'Adding container for {needed_compiler} '
                  f'on {c.ubuntu} with gcc {c.gcc} and clang {c.clang}')
            c.add()
            return
        if c.clang and 'clang-' + c.clang == needed_compiler:
            if c.exists:
                sys.exit(f'[!] ERROR: container with the compiler'
                         f'{needed_compiler} already exists!')
            print(f'Adding container for {needed_compiler} '
                  f'on {c.ubuntu} with gcc {c.gcc} and clang {c.clang}')
            c.add()
            return
    sys.exit(f'[!] ERROR: no container with the compiler "{needed_compiler}"')

def remove_handler(removed_compiler, containers) -> None:
    """Removes the specified container(s) based on the provided compiler"""
    if removed_compiler == 'all':
        for c in containers:
            if c.exists:
                print(f'Removing container for {removed_compiler} '
                      f'on {c.ubuntu} with gcc {c.gcc} and clang {c.clang}')
                c.rm()
        return
    sys.exit('[!] ERROR: no container with the compiler "{needed_compiler}"')

def main():
    """Main function to manage the containers"""

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
                 'clang-7',
                 'clang-8',
                 'clang-9',
                 'clang-10',
                 'clang-11',
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
    parser.add_argument('-a', '--add', choices=compilers, metavar='compiler',
                        help=f'build a container with this compiler: ({", ".join(compilers)}, or "all" to build with all of them)')
    parser.add_argument('-r', '--remove', choices=['all'], metavar='all',
                        help='remove all created containers')
    args = parser.parse_args()

    if not any([args.list, args.add, args.remove]):
        parser.print_help()
        sys.exit(1)
    if args.add and args.remove:
        print("Really? Adding and deleting at the same time doesnt make sense!")
        sys.exit(1)
    global SUDO_CMD
    SUDO_CMD = check_group()


    containers = []
    containers += [Container("4.9", None, "16.04")]
    containers += [Container("5", None, "16.04")]
    containers += [Container("6", "7", "18.04")]
    containers += [Container("7", "8", "18.04")]
    containers += [Container("8", "9", "20.04")]
    containers += [Container("9", "10", "20.04")]
    containers += [Container("10", "11", "20.04")]
    containers += [Container("11", "12", "22.04")]
    containers += [Container("12", "13", "22.04")]
    containers += [Container("12", "14", "22.04")]
    containers += [Container("13", "15", "23.04")]
    containers += [Container("14", "16", "24.04")]
    containers += [Container("14", "17", "24.04")]

    if args.list:
        for c in containers:
            if c.exists:
                status = '[+]'
            else:
                status = '[-]'
            print(f'container with gcc {c.gcc} and clang {c.clang} on ubuntu {c.ubuntu}: {status}')
        sys.exit(0)

    if args.add:
        add_handler(args.add,containers)
        sys.exit(0)
    elif args.remove:
        remove_handler(args.remove,containers)
        sys.exit(0)


if __name__ == '__main__':
    main()
