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
                'all-gcc',
                'all-clang',
                'all']

SUDO_CMD = ''

class Container:
    """
    Represents a Docker container configured for kernel building.

    Attributes:
        gcc (str): Version of GCC compiler.
        clang (str): Version of Clang compiler (optional).
        ubuntu (str): Version of Ubuntu.
        id (str): Docker image id.
        exists (bool): Whether the container is built.
    """
    def __init__(self, gcc_version, clang_version, ubuntu_version):
        self.gcc = gcc_version
        self.clang = clang_version
        self.ubuntu = ubuntu_version
        self.id = self.check()
        self.tag_gcc = None
        self.tag_clang = None

    def add(self, mode):
        if self.id:
            if self.tag_gcc:
                subprocess.run(['docker', 'tag', self.id, f'kernel-build-container:clang-{self.clang}'])
                return
            if self.clang:
                subprocess.run(['docker', 'tag', self.id, f'kernel-build-container:clang-{self.gcc}'])
                return

        """Builds the Docker container with the specified compiler"""
        build_args=['--build-arg', f'UBUNTU_VERSION={self.ubuntu}',
                    '--build-arg', f'UNAME={os.getlogin()}',
                    '--build-arg', f'UID={os.getuid()}',
                    '--build-arg', f'GID={os.getgid()}'
        ]
        if self.clang:
            build_args=['--build-arg', f'CLANG_VERSION={self.clang}']+build_args
            if mode=='clang' or mode=='all':
                build_args=build_args+['-t', f'kernel-build-container:clang-{self.clang}']
        if self.gcc:
            build_args=['--build-arg', f'GCC_VERSION={self.gcc}',]+build_args
            if mode=='gcc' or mode=='all':
                build_args=build_args+['-t', f'kernel-build-container:clang-{self.gcc}']  
        subprocess.run([SUDO_CMD, 'docker', 'build', *build_args, '.'],
                        text=True, check=True)
        self.check()

    def rm(self):
        """Removes the Docker container"""      
        subprocess.run([SUDO_CMD, 'docker', 'rmi', '-f', self.id],
                        text=True, check=True)
        self.check()

    def check(self):
        """Checks if the Docker container exists and chains id to the class"""
        search_gcc = [f'kernel-build-container:gcc-{self.gcc}']
        search_clang = [f'kernel-build-container:clang-{self.clang}']
        cmd1 = subprocess.run([SUDO_CMD, 'docker', 'images', *search_gcc, '--format', '{{.ID}},{{.TAG}}'],
                                stdout=subprocess.PIPE,
                                text=True, check=True)
        cmd2 = subprocess.run([SUDO_CMD, 'docker', 'images', *search_clang, '--format', '{{.ID}},{{.TAG}}'],
                        stdout=subprocess.PIPE,
                        text=True, check=True)
        if cmd1:
            id_,self.tag_gcc = cmd1.stdout.split(",")
        if cmd2:
            id_,self.tag_clang = cmd1.stdout.split(",")
        container_id=id_
        return container_id.strip()

def check_group():
    """Checks if the user is in the Docker group, returns 'sudo' if not"""
    result = subprocess.run(['groups'], capture_output=True,
                            text=True, check=True)
    if 'docker' in result.stdout or 'root' in result.stdout:
        return ''
    print('We need to use sudo for running docker')
    return 'sudo'

def add_handler(needed_compiler, containers):
    """Adds the specified container(s) based on the provided compiler"""
    if needed_compiler == 'all':
        for c in containers:
            if not c.id:
                print(f'Adding {c.ubuntu} container with gcc {c.gcc} and clang {c.clang}')
                c.add('all')
        return
    if needed_compiler == 'all_gcc':
        for c in containers:
            if not c.id:
                print(f'Adding {c.ubuntu} container with gcc {c.gcc}')
                c.add('gcc')
        return
    if needed_compiler == 'all_clang':
        for c in containers:
            if not c.id:
                print(f'Adding {c.ubuntu} container with clang {c.clang}')
                c.add('clang')
        return
    for c in containers:
        if 'gcc-' + c.gcc == needed_compiler:
            if c.id:
                sys.exit(f'[!] ERROR: container with the compiler'
                         f'{needed_compiler} already exists!')
            print(f'Adding {c.ubuntu} container with gcc {c.gcc} and clang {c.clang}')
            c.add()
            return
        if c.clang and 'clang-' + c.clang == needed_compiler:
            if c.id:
                sys.exit(f'[!] ERROR: container with the compiler'
                         f'{needed_compiler} already exists!')
            print(f'Adding {c.ubuntu} container with gcc {c.gcc} and clang {c.clang}')
            c.add()
            return

def remove_handler(removed_compiler, containers) -> None:
    """Removes the specified container(s) based on the provided compiler"""
    if removed_compiler == 'all':
        running = subprocess.run(f"{SUDO_CMD} docker ps | grep 'kernel-build-container' | awk '{{print $1}}'", 
                                shell=True, text=True, check=True, stdout=subprocess.PIPE).stdout.split()

        if running:
            sys.exit('You still have running containers:\n' + '\n'.join(running))
        for c in containers:
            if c.id:
                print(f'Removing container for {removed_compiler} '
                      f'on {c.ubuntu} with gcc {c.gcc} and clang {c.clang}')
                c.rm()

def main():
    """Main function to manage the containers"""
    parser = argparse.ArgumentParser(description='Manage the kernel-build-containers')
    parser.add_argument('-l','--list', action='store_true',
                        help='show the kernel build containers')
    parser.add_argument('-a', '--add', choices=compilers, metavar='compiler',
                        help=f'build a container with this compiler: ({", ".join(compilers)}, where'
                              ' "all" for all of the compilers)')
    parser.add_argument('-r', '--remove', choices=['all'], metavar='all',
                        help='remove all created containers')
    args = parser.parse_args()

    if not any([args.list, args.add, args.remove]):
        parser.print_help()
        sys.exit(1)
    if args.add and args.remove:
        print("Adding and removing at the same time doesn't make sense!")
        sys.exit(1)

    globals()["SUDO_CMD"] = check_group()

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
        for c in containers:
            if c.id:
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
