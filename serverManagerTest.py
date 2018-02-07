import multiprocessing, time, sys, random
import datetime as dt
from multiprocessing.managers import BaseManager


def rov():
    mgr = ROVManager(role='client', address='127.0.0.1')
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
        if time.time()-start > 3:
            sensor_values.update({'exit': True})
            break
        sys.stdout.write('\r{}'.format(sensor_values))
        time.sleep(0.05)


def start_server():
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

    def fun(self):
        return self.sensor_values()



if __name__ == '__main__':

    serv = multiprocessing.Process(target=start_server)
    p1 = multiprocessing.Process(target=rov)
    p2 = multiprocessing.Process(target=reader)
    processes = [serv, p1, p2]

    for p in processes:
        p.start()

    mgr = ROVManager(role='client', address='127.0.0.1')

    while mgr.sensor_values().get('exit') is False:
        time.sleep(0.05)
    print('\nShutting down server')
    time.sleep(1)
    serv.terminate()
