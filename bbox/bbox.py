from butter.clone import \
    unshare, CLONE_NEWNS, CLONE_NEWUTS, CLONE_NEWIPC, CLONE_NEWUSER, \
    CLONE_NEWPID, CLONE_NEWNET
from butter.system import mount, pivot_root, umount, \
    MS_BIND, MS_NOSUID, MS_RDONLY, MS_REMOUNT
from os import \
    chdir, execve, fork, getegid, geteuid, mkdir, path, rmdir, \
    setresgid, setresuid, waitpid
from shutil import copyfile
from socket import sethostname

MNT_DETACH = 2

def bind_mount(src, target):
    try:
        mkdir(target)
    except FileExistsError:
        pass
    mount(src, target, '', MS_BIND | MS_NOSUID)
    mount(src, target, '', MS_BIND | MS_NOSUID | MS_RDONLY | MS_REMOUNT)

def write_file(file, data):
    with open(file, 'wb') as f:
        f.write(data)

def init():
    host_euid = geteuid()
    host_egid = getegid()
    unshare(CLONE_NEWNS | CLONE_NEWUTS | CLONE_NEWIPC |
            CLONE_NEWUSER | CLONE_NEWPID | CLONE_NEWNET)
    pid = fork()
    if pid:
        waitpid(pid, 0)
        exit()
    write_file('/proc/self/uid_map', '0 {} 1'.format(host_euid).encode())
    try:
        write_file('/proc/self/setgroups', b'deny')
    except FileNotFoundError:
        pass
    write_file('/proc/self/gid_map', '0 {} 1'.format(host_egid).encode())
    setresuid(0, 0, 0)
    setresgid(0, 0, 0)
    sethostname('bbox')

    mount('tmpfs', '/tmp', 'tmpfs', MS_NOSUID, 'size=16m,nr_inodes=4k')
    bind_mount('/bin', '/tmp/bin')
    bind_mount('/etc', '/tmp/etc')
    bind_mount('/lib', '/tmp/lib')
    bind_mount('/lib64', '/tmp/lib64')
    mkdir('/tmp/proc')
    mount('proc', '/tmp/proc', 'proc', MS_NOSUID)
    mkdir('/tmp/root')
    copyfile('root/a.out', '/tmp/root/a.out')
    write_file('/tmp/root/a.dat', b'Happy holidays 2019!  Password: 67160709\n')
    bind_mount('root', '/tmp/root')
    bind_mount('/sbin', '/tmp/sbin')
    bind_mount('/usr', '/tmp/usr')
    chdir('/tmp')
    mkdir('old_root')
    pivot_root('.', 'old_root')
    umount('old_root', MNT_DETACH)
    rmdir('old_root')
    mount('/', '/', '', MS_BIND | MS_NOSUID)
    mount('/', '/', '', MS_BIND | MS_NOSUID | MS_RDONLY | MS_REMOUNT)
    chdir('/root')

    pid = fork()
    if pid:
        waitpid(pid, 0)
        return
    execve(
        '/bin/bash',
        ['bbox'],
        {'HOME': '/root', 'PATH': '/usr/sbin:/usr/bin:/sbin:/bin'})

if __name__ == '__main__':
    init()
