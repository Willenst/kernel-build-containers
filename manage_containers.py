import os
import subprocess
import argparse
import sys

gcc_containers = {
    'gcc-4.9' : 'ubuntu-16.04',
    'gcc-5' : 'ubuntu-16.04',
    'gcc-6' : 'ubuntu-18.04',
    'gcc-7' : 'ubuntu-18.04',
    'gcc-8' : 'ubuntu-20.04',
    'gcc-9' : 'ubuntu-20.04',
    'gcc-10' : 'ubuntu-20.04',
    'gcc-11' : 'ubuntu-22.04',
    'gcc-12' : 'ubuntu-22.04',
    'gcc-13' : 'ubuntu-23.04',
    'gcc-14' : 'ubuntu-24.04'
}


clang_containers = {
    'clang-12':'gcc-11',
    'clang-13':'gcc-11',
    'clang-14':'gcc-12',
    'clang-15':'gcc-13',
    'clang-16':'gcc-14',
    'clang-17':'gcc-14',
}

def check_group():
    result = subprocess.run(['groups'], capture_output=True, text=True)
    return 'docker' in result.stdout or 'root' in result.stdout

if check_group():
    SUDO_CMD = ""
else:
    print("Hey, we gonna use sudo for running docker")
    SUDO_CMD = "sudo"

def createParser():
    containers = list(gcc_containers.keys()) + list(clang_containers.keys())
    containers += ['All']
    modes = ['build','remove']
    parser = argparse.ArgumentParser()
    parser.add_argument ('-c', '--container',
                         choices=containers,
                         nargs='+',
                         required=True,
                         help='Supported versions (\'all\' to build/remove all of them): {}'.format(', '.join(containers)))
    parser.add_argument ('-m', '--mode', choices=modes, required=True,
                         help='Chose one of the supported modes: {}'.format(', '.join(modes)))
    parser.add_argument ('-l','--list', action='store_true', help='Show containers and exit.')
    args = parser.parse_args()
    if args.list:
        print("not implemented yet")
        sys.exit()
    if 'All' in args.container:
        print("not implemented yet")
        sys.exit()
    return parser

def build_container(gcc_version,clang_version):
    ubuntu_version=gcc_containers[f'gcc-{gcc_version}'].split('-')[1]
    build_args=['--build-arg', f'GCC_VERSION={gcc_version}',
                '--build-arg', f'UBUNTU_VERSION={ubuntu_version}',
                '--build-arg', f'UNAME={os.getlogin()}',
                '--build-arg', f'UID={os.getuid()}',
                '--build-arg', f'GID={os.getgid()}'
    ]
    if clang_version:
        print(f"\nbuilding_clang_container with clang-{clang_version} gcc-{gcc_version} ubuntu-{ubuntu_version}")
        subprocess.run([SUDO_CMD, 'docker', 'build', '--build-arg', f'CLANG_VERSION={clang_version}',
                         *build_args, '-t', f'kernel-build-container:clang-{clang_version}', '.'], text=True)
    else:
        print(f"\nbuilding_gcc_container with gcc-{gcc_version} ubuntu-{ubuntu_version}")
        subprocess.run([SUDO_CMD, 'docker', 'build', *build_args, '-t', f'kernel-build-container:gcc-{gcc_version}', '.'], text=True)

def remove_container(container_name):
    subprocess.run([SUDO_CMD, 'docker', 'rmi', f'kernel-build-container:{container_name}'], text=True)
    print(f'\nRemoved container {container_name}\n')

if __name__ == '__main__':

    parser = createParser()
    namespace = parser.parse_args(sys.argv[1:])
    try:
        containers = namespace.container
        mode = namespace.mode
    except:
        raise Exception('parsing went wrong')
    if mode == 'build':
        for container in containers:
            if container.startswith('clang'):
                clang_version = container.split('-')[1]
                gcc_version = clang_containers[f'clang-{clang_version}'].split('-')[1]
                build_container(gcc_version,clang_version)
            elif container.startswith('gcc'):
                gcc_version = container.split('-')[1]
                build_container(gcc_version,None)
            else:
                raise Exception('wrong param')
    elif mode == 'remove':
        for container in containers:
            remove_container(container)
