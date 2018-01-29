#!/usr/bin/env python3
# Foundations of Python Network Programming, Third Edition
# https://github.com/brandon-rhodes/fopnp/blob/m/py3/chapter03/tcp_sixteen.py
# Simple TCP client and server that send and receive 16 octets

import argparse, socket, time, os

def recvall(sock):
    start = time.time()
    length = int(sock.recv(10),16)
    data = b''
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError('was expecting %d bytes but only received'
                           ' %d bytes before the socket closed'
                           % (length, len(data)))
        data += more
    end = (time.time()-start)*1000
    print('{} MB took {} ms'.format(len(data)/1000000,end))
    with open(os.path.join(os.path.dirname(__file__),'log.log'), 'a+') as logfile:
        logfile.write('{},{}\r'.format(len(data)/1000000, end))
    return data

def sendall_(data, sock):
    length = "{0:#0{1}x}".format(len(data),10).encode()
    sock.sendall(length+data)

def server(interface, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((interface, port))
    sock.listen(1)
    print('Listening at', sock.getsockname())
    while True:
        print('Waiting to accept a new connection')
        sc, sockname = sock.accept()
        print('We have accepted a connection from', sockname)
        print('  Socket name:', sc.getsockname())
        print('  Socket peer:', sc.getpeername())
        message = recvall(sc)
        with open('flower_recv.jpg','wb') as file:
            file.write(message)
        sendall_(b'Farewell, client',sc)
        sc.close()
        print('  Reply sent, socket closed')
        with open(os.path.join(os.path.dirname(__file__),'log.log'), 'r') as logfile:
            mbs = 0
            time_tot = 0
            for i, line in enumerate(logfile.readlines()):
                mb, time = line.split(',')
                mbs += float(mb)
                time_tot += float(time)
            print('Avg: {:.2} MB/s of {} tries'.format(mbs/time_tot, i))

def client(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    print('Client has been assigned socket name', sock.getsockname())
    # with open('flower.jpg','rb') as file:
    #     sendall_(file.read(), sock)
    msg = b'#'*5*1000000
    print('sending {} MB'.format(len(msg)/1000000))
    sendall_(msg, sock)
    reply = recvall(sock)
    print('The server said', repr(reply))
    sock.close()

if __name__ == '__main__':
    choices = {'client': client, 'server': server}
    parser = argparse.ArgumentParser(description='Send and receive over TCP')
    parser.add_argument('role', choices=choices, help='which role to play')
    parser.add_argument('host', help='interface the server listens at;'
                        ' host the client sends to')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060,
                        help='TCP port (default 1060)')
    args = parser.parse_args()
    function = choices[args.role]
    function(args.host, args.p)
