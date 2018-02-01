import argparse, socket
from network_support import find_server

def recvall(sock):
    length = int(sock.recv(10),16)
    data = b''
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError('was expecting %d bytes but only received'
                           ' %d bytes before the socket closed'
                           % (length, len(data)))
        data += more
    return data

def sendall_(data, sock):
    length = "{0:#0{1}x}".format(len(data),10).encode()
    sock.sendall(length+data)

def client(host):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if host == "":
        host = find_server(1060)
    sock.connect((host, 1060))
    print('Client has been assigned socket name', sock.getsockname())
    msg = b'hey there server'
    print('sending {} MB'.format(len(msg)/1000000))
    sendall_(msg, sock)
    reply = recvall(sock)
    print('The server said', repr(reply))
    sock.close()

def server(host):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, 1060))
    sock.listen(1)
    print('Listening at', sock.getsockname())
    print('Client should connect to {}'
          .format(socket.gethostbyname(socket.gethostname())))
    while True:
        print('Waiting to accept a new connection')
        sc, sockname = sock.accept()
        print('We have accepted a connection from', sockname)
        print('  Socket name:', sc.getsockname())
        print('  Socket peer:', sc.getpeername())
        message = recvall(sc)
        print('server says: {}'.format(message.decode()))
        sendall_(b'Farewell, client',sc)
        sc.close()
        print('  Reply sent, socket closed')

if __name__ == '__main__':
    choices = {'client': client, 'server': server}
    parser = argparse.ArgumentParser(description='Send and receive over TCP')
    parser.add_argument('role', choices=choices, help='which role to play')
    parser.add_argument('host', help='interface the server listens at;'
                        ' host the client sends to')
    args = parser.parse_args()
    function = choices[args.role]
    function(args.host)
