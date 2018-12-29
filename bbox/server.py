import os
import pty
import select
import socket
import threading
import time
from . import bbox

def poll(connection, pty_fd, pid):
    try:
        sock_fd = connection.fileno()
        pty_data = b''
        sock_data = b''
        cost = 0
        while True:
            r = list()
            w = list()
            if pty_data:
                w.append(sock_fd)
            else:
                r.append(pty_fd)
            if sock_data:
                w.append(pty_fd)
            else:
                r.append(sock_fd)
            r, w, _ = select.select(r, w, [])
            if sock_fd in r:
                data = os.read(sock_fd, 4096)
                if not data:
                    return
                sock_data += data
            if pty_fd in r:
                data = os.read(pty_fd, 4096)
                if not data:
                    return
                pty_data += data
            if sock_fd in w:
                os.write(sock_fd, pty_data)
                cost += len(pty_data)
                pty_data = b''
            if pty_fd in w:
                os.write(pty_fd, sock_data)
                cost += len(sock_data)
                sock_data = b''
            if cost > 1024:
                time.sleep(cost / 102400)
                cost = 0
    except OSError:
        pass
    finally:
        os.close(pty_fd)
        connection.close()
        os.kill(pid, 9)
        os.waitpid(pid, 0)

def handle(connection):
    pid, pty_fd = pty.fork()
    if not pid:
        connection.close()
        bbox.init()
        exit()
    os.set_inheritable(pty_fd, False)
    threading.Thread(target=lambda: poll(connection, pty_fd, pid)).start()

def main():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.set_inheritable(False)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(('0.0.0.0', 2019))
    listener.listen()
    while True:
        connection, address = listener.accept()
        connection.set_inheritable(False)
        connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        print('accepted ' + ':'.join(map(str, address)))
        handle(connection)

if __name__ == '__main__':
    main()
