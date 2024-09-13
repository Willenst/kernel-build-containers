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
             'clang-5.0',
             'clang-6.0',
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

class Container:
    """
    Represents a Docker container configured for kernel building.

    Class Attributes:
        sudo (str): represents sudo command
        quiet (bool): enable quiet option in Docker

    Container Attributes:
        gcc (str): Version of GCC compiler.
        clang (str): Version of Clang compiler (optional).
        ubuntu (str): Version of Ubuntu.
        id (str): Docker image id.
    """

    sudo = ''
    quiet = False

    def __init__(self, gcc_version, clang_version, ubuntu_version):
        self.gcc = gcc_version
        self.clang = clang_version
        self.ubuntu = ubuntu_version
        self.id = self.check()

    def add(self):
        """Builds the Docker container with the specified compilers"""
        build_args = ['--build-arg', f'GCC_VERSION={self.gcc}',
                      '--build-arg', f'UBUNTU_VERSION={self.ubuntu}',
                      '--build-arg', f'UNAME={os.getlogin()}',
                      '--build-arg', f'UID={os.getuid()}',
                      '--build-arg', f'GID={os.getgid()}',
                      '-t', f'kernel-build-container:gcc-{self.gcc}'
        ]
        if self.clang:
            build_args = ['--build-arg', f'CLANG_VERSION={self.clang}']+build_args+ \
                         ['-t', f'kernel-build-container:clang-{self.clang}']
        if self.quiet:
            build_args = build_args + ['-q']
        subprocess.run([self.sudo, 'docker', 'build', *build_args, '.'],
                        text=True, check=True)
        self.check()

    def rm(self):
        """Removes the Docker container if it exists and not running"""
        running = subprocess.run(f"{Container.sudo} docker ps | "
                                 f"grep -E 'kernel-build-container:"
                                 f"(gcc-{self.gcc}|clang-{self.clang})' || true",
                                 shell=True, text=True, check=True, stdout=subprocess.PIPE).stdout
        print("AAAAAA", len(running))
        if not running:
            subprocess.run([self.sudo, 'docker', 'rmi', '-f', self.id],
                            text=True, check=True)
            self.check()
            return ''
        return running

    def check(self):
        """Checks if the Docker container exists and parse id"""
        search = [f'kernel-build-container:gcc-{self.gcc}']
        if self.clang:
            search = [f'kernel-build-container:clang-{self.clang}']
        cmd = subprocess.run([self.sudo, 'docker', 'images', *search, '--format', '{{.ID}}'],
                              stdout=subprocess.PIPE,
                              text=True, check=True)
        self.id = cmd.stdout.strip()
        return self.id

def check_group():
    """Checks if the user is in the Docker group, returns 'sudo' if not"""
    result = subprocess.run(['groups'], capture_output = True,
                            text = True, check = True)
    if 'docker' in result.stdout:
        return ''
    print('We need to use sudo for running docker')
    return 'sudo'

def add_handler(needed_compiler, containers):
    """Adds the specified container(s) based on the provided compiler or add all of them"""
    if needed_compiler == 'all':
        for c in containers:
            if not c.id:
                print(f'Adding ubuntu {c.ubuntu} container with gcc {c.gcc} and clang {c.clang}')
                c.add()
        return
    for c in containers:
        print(c.id)
        if 'gcc-' + c.gcc == needed_compiler:
            if c.id:
                sys.exit(f'[!] ERROR: container with {needed_compiler} already exists!')
            print(f'Adding {c.ubuntu} container with gcc {c.gcc} and clang {c.clang}')
            c.add()
            return
        if c.clang and 'clang-' + c.clang == needed_compiler:
            if c.id:
                sys.exit(f'[!] ERROR: container with {needed_compiler} already exists!')
            print(f'Adding {c.ubuntu} container with gcc {c.gcc} and clang {c.clang}')
            c.add()
            return

def remove_handler(containers) -> None:
    """Removes container images"""
    out = ''
    for c in containers:
        if c.id:
            print(f'Removing container on {c.ubuntu} with gcc {c.gcc} and clang {c.clang}')
            out = out + c.rm()
    if out:
        print('\nyou still have running containers, that can\'t be removed:\n', out)

def list_containers(containers):
    """Print built containers"""
    for c in containers:
        c.check()
        if c.id:
            status = '[+]'
        else:
            status = '[-]'
        print(f'container with gcc {c.gcc} and clang {c.clang} on ubuntu {c.ubuntu}: {status}')
    sys.exit(0)

def main():
    """Main function to manage the containers"""
    parser = argparse.ArgumentParser(description='Manage the kernel-build-containers')
    parser.add_argument('-l','--list', action = 'store_true',
                        help = 'show the kernel build containers')
    parser.add_argument('-a', '--add', choices = compilers, metavar = 'compiler',
                        help=f'build a container with this compiler: ({", ".join(compilers)},'
                              'where "all" for all of the compilers)')
    parser.add_argument('-r', '--remove', choices = ['all'], metavar = 'all',
                        help = 'remove all created containers')
    parser.add_argument('-q','--quiet', action = 'store_true',
                        help = 'suppress container build output')
    args = parser.parse_args()

    if not any([args.list, args.add, args.remove, args.quiet]):
        parser.print_help()
        sys.exit(1)
    if bool(args.list) + bool(args.add) + bool(args.remove) > 1:
        sys.exit("Combining these options doesn't make sense")

    Container.sudo = check_group()
    if args.quiet:
        Container.quiet = True

    containers = []
    containers += [Container("4.9", "5.0", "16.04")]
    containers += [Container("5", "6.0", "16.04")]
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
        list_containers(containers)

    if args.add:
        add_handler(args.add, containers)
        list_containers(containers)

    if args.remove:
        remove_handler(containers)
        list_containers(containers)

if __name__ == '__main__':
    main()
