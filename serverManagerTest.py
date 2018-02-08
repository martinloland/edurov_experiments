import multiprocessing, time, sys, random, argparse, socket
import datetime as dt
from multiprocessing.managers import BaseManager


def rov(address='127.0.0.1'):
    mgr = ROVManager(role='client', address=address)
    sensor_values = mgr.sensor_values()

    while sensor_values.get('exit') is False:
        sensor_values.update({'time': dt.datetime.now().isoformat(),
                              'voltage': random.randrange(10)})
        time.sleep(0.001)


def reader():
    start = time.time()
    mgr = ROVManager(role='client', address='127.0.0.1')
    sensor_values = mgr.sensor_values()

    while True:
        if time.time()-start > 30:
            sensor_values.update({'exit': True})
            break
        sys.stdout.write('\r{}'.format(sensor_values))
        time.sleep(0.05)


def start_server():
    print('Client should connect to {}'
          .format(socket.gethostbyname(socket.gethostname())))
    mgr = ROVManager(role='server')


class ROVManager(BaseManager):
    def __init__(self, role, address='0.0.0.0', port=5050, authkey=b'abc'):
        if role not in ['server', 'client']:
            raise ValueError("""role has to be 'server' or 'client'""")
        if role == 'client' and address == '0.0.0.0':
            raise ValueError('A client can not connect to all ports')

        super(ROVManager, self).__init__(address=(address, port),
                                         authkey=authkey)
        if role is 'server':
            self.sensor_values = {'exit': False}
            self.register('sensor_values', callable=lambda:self.sensor_values)
            server = self.get_server()
            server.serve_forever()
        elif role is 'client':
            self.register('sensor_values')
            self.connect()


if __name__ == '__main__':
    choices = {'client': 'client', 'server': 'server'}
    parser = argparse.ArgumentParser(description='Communicate with Manager')
    parser.add_argument('role', choices=choices, help='which role to play')
    parser.add_argument('-ip', help='ip the client connects to')
    args = parser.parse_args()

    if args.role == 'server':
        p0 = multiprocessing.Process(target=start_server)
        p2 = multiprocessing.Process(target=reader)
        p0.start()
        p2.start()

        mgr = ROVManager(role='client', address='127.0.0.1')

        while mgr.sensor_values().get('exit') is False:
            time.sleep(0.05)

        print('\nShutting down server')
        time.sleep(1)
        p0.terminate()

    elif args.role == 'client':
        p1 = multiprocessing.Process(target=rov, args=(args.ip,))
        p1.start()
