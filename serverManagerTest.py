import multiprocessing, time, sys, random
import datetime as dt
from multiprocessing.managers import BaseManager

def rov():
    mgr = BaseManager(address=('127.0.0.1',5050), authkey=b'abc')
    mgr.register('sensor_values')
    mgr.connect()
    sensor_values = mgr.sensor_values()
    while sensor_values.get('exit') is False:
        sensor_values.update({'time':dt.datetime.now().isoformat(),
                              'voltage':random.randrange(10)})
        time.sleep(0.001)

def reader():
    start = time.time()
    mgr = BaseManager(address=('127.0.0.1',5050), authkey=b'abc')
    mgr.connect()
    mgr.register('sensor_values')
    mgr.connect()
    sensor_values = mgr.sensor_values()

    while True:
        if time.time()-start > 5:
            sensor_values.update({'exit':True})
            break
        sys.stdout.write('\r{}'.format(sensor_values))
        time.sleep(0.05)

if __name__ == '__main__':
    mgr = BaseManager(address=('0.0.0.0',5050), authkey=b'abc')
    sensor_values = {'exit':False}
    mgr.register('sensor_values', callable=lambda:sensor_values)
    server = mgr.get_server()

    p1 = multiprocessing.Process(target=rov)
    p2 = multiprocessing.Process(target=reader)
    processes = [p1, p2]

    for p in processes:
        p.start()
    server.serve_forever()
    for p in processes:
        p.join()
