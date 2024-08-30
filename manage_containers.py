import os
import subprocess
import argparse
import sys
import re
#раскраска вывода
GREEN_COLOR = '\x1b[32m'
RED_COLOR = '\x1b[31m'
COLOR_END = '\x1b[0m'
#закладка данных по контейнеры
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
#таблица совместимости
clang_gcc_compat = {
    'clang-6' : ['gcc-8','gcc-9','gcc-10'], #20.04
    'clang-7' : ['gcc-8','gcc-9','gcc-10'], #20.04
    'clang-8' : ['gcc-8','gcc-9','gcc-10'], #20.04
    'clang-9' : ['gcc-8','gcc-9','gcc-10'], #20.04
    'clang-10' : ['gcc-8','gcc-9','gcc-10'], #20.04
    'clang-11' : ['gcc-9','gcc-10','gcc-11','gcc-12'], #22.04
    'clang-12' : ['gcc-8','gcc-9','gcc-10','gcc-11','gcc-12'], #20.04, 22.04
    'clang-13' : ['gcc-9','gcc-10','gcc-11','gcc-12','gcc-13'], #22.04 23.04
    'clang-14' : ['gcc-9','gcc-10','gcc-11','gcc-12','gcc-13'], #22.04 23.04 24.04
    'clang-15' : ['gcc-9','gcc-10','gcc-11','gcc-12','gcc-13'], #22.04 23.04 24.04
    'clang-16' : ['gcc-13','gcc-14'], #23.04 24.04
    'clang-17' : ['gcc-13','gcc-14'], #23.04 24.04
    'clang-18' : ['gcc-14'] #24.04
}
#проверка группы, решил закинуть в отдельную функцию
def check_group():
    result = subprocess.run(['groups'], capture_output=True, text=True)
    if 'docker' in result.stdout:
        return ''
    else:
        print("Hey, we gonna use sudo for running docker")
        return 'sudo'
#парсер, его немного переделал
def createParser():
    containers = list(gcc_containers.keys()) + list(clang_gcc_compat.keys())
    containers += ['All']
    parser = argparse.ArgumentParser()
#валидатор входных данных, принимает clang-X, gcc-X, clang-X+gcc-Y, gcc-Y+clang-X
#обработки неверных входных данных как таковой пока что нет, но она в планах!
    def validate_input(value):
        pattern = re.compile(r'(clang-\d+\+gcc-\d+)|(gcc-\d+\+clang-\d+)|(clang-\d+)|(gcc-\d+)')
        if not pattern.match(value):
            raise argparse.ArgumentTypeError(f"Invalid value '{value}'.")
        return value
#Тут отдельные аргументы под постройку и удаление контейнеров
    parser.add_argument ('-a', '--add',
                         type=validate_input,
                         nargs='+',
                         required=False,
                         help='Add container with compiler \'gcc-X\' or '
                              '\'clang-Y+gcc-X\' (or \'clang-X\' to autochoose gcc),'
                              'write \'all\' to build all at once')
    parser.add_argument ('-r', '--remove',
                        type=validate_input,
                        nargs='+',
                        required=False,
                        help='Remove container with compiler \'gcc-X\' or '
                             '\'clang-Y+gcc-X\' (or \'clang-X\' to autochoose gcc),'
                             'write \'all\' to remove all at once')
    parser.add_argument ('-l','--list', action='store_true', help='Show supported compilers')
    return parser

#постройка контейнеров, практически не менялась
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
                         *build_args, '-t', f'kernel-build-container:clang-{clang_version}+gcc-{gcc_version}', '.'], text=True)
    else:
        print(f"\nbuilding_gcc_container with gcc-{gcc_version} ubuntu-{ubuntu_version}")
        subprocess.run([SUDO_CMD, 'docker', 'build', *build_args, '-t', f'kernel-build-container:gcc-{gcc_version}', '.'], text=True)

def remove_container(container_name):
    subprocess.run([SUDO_CMD, 'docker', 'rmi', f'kernel-build-container:{container_name}'], text=True)
    print(f'\nRemoved container {container_name}\n')
#функция под захват всех сделанных контейнеров из системы
def extract_containers():
    containers = subprocess.run([SUDO_CMD, 'docker', 'images', '--format', '{{.Tag}}'], 
                        stdout=subprocess.PIPE, 
                        text=True)
    compilers=containers.stdout.strip().split()
    return compilers
#функция под вывод контейнеров, это очень далеко не ее финальный вид, пока что это просто затычка
#сейчас я думаю сделать столбик контейнеров gcc
#затем столбик контейнеров clang, у них будут отдельно выведены совместимые gcc
#затем столбик собранных контейнеров
#если gcc или clang где то используются (неважно, отдельно, вместе), они будут гореть зеленым и будут помечены "+"
#также их будет само собой отображать в сбилженном контейнере в столбике контейнеров
def list_containers(): 
    all_containers = list(gcc_containers.keys())
    current_containers = extract_containers()
    for el in all_containers:
        if el in current_containers:
            color=GREEN_COLOR
            print(color+'[+] '+el+COLOR_END)
        else:
            color=RED_COLOR
            print(color+'[-] '+el+COLOR_END)
#Парсинг версии gcc/clang, вход не важен, будет работать как для их комбинации такк и под отдельные
def parse_versions(text):
    #actualy need to refactor this
    clang_version = re.findall(r'clang-(\d+)', text)
    gcc_version = re.findall(r'gcc-(\d+)', text)
    if clang_version:
        clang = clang_version[0]
    else: 
        clang = None
    if gcc_version:
        gcc = gcc_version[0]
    else: 
        gcc = None
    return clang, gcc
#проверка совместимости, будет оповещать если юзер выбрал неподходящие версии gcc и clang
def comtability_check(gcc_version,clang_version):
    available_gcc_versions = clang_gcc_compat[f'clang-{clang_version}']
    gcc = f'gcc-{gcc_version}'
    if gcc in available_gcc_versions:
        return True
    else:
        print(f'Incompatible gcc and clang, for clang-{clang_version}, choosee gcc from ' + ', '.join(available_gcc_versions))
        sys.exit()
#обработчик вхорда, работает под комбинированный и отдельный вход
def add_handler(add):
    for compiler in add:
        if compiler in extract_containers():
            print(compiler+' already added')
            continue
        if compiler == 'all':
            print('not implemented yet!') #сборку всех сразу сделаю позже
            sys.exit()

        gcc_version, clang_version = parse_versions(compiler)

        if clang_version and gcc_version:
            if comtability_check(gcc_version,clang_version):
                build_container(gcc_version,clang_version)

        elif clang_version: #automated gcc chose
            gcc_version = clang_gcc_compat[f'clang-{clang_version}']
            build_container(gcc_version[-1],clang_version)

        elif gcc_version:
            build_container(gcc_version,None)
#обработчик удаления, должен работать по тегу контейнера
def remove_handler(remove):
    for compiler in remove:
        if compiler == 'all':
            print('not implemented yet!') #удаление всех сразу сделаю позже
            sys.exit()
        if compiler in extract_containers():
            remove_container(compiler)
        else:
            print('No such container :',compiler)


if __name__ == '__main__':

    parser = createParser()
    args = parser.parse_args()
    SUDO_CMD = check_group()
    add = args.add
    remove = args.remove
    if args.list:
        print('DEMO! IN DEVELOPMENT!')
        list_containers()
        sys.exit()
    if add:
        add_handler(add)
    if remove:
        remove_handler(remove)

