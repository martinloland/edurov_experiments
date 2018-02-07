import multiprocessing, time, sys, random
import datetime as dt

def rov(sensor_values):
    while sensor_values['exit'] is False:
        sensor_values.update({'time':dt.datetime.now().isoformat(),
                              'voltage':random.randrange(10)})
        time.sleep(0.001)

def reader(sensor_values):
    start = time.time()
    while True:
        if time.time()-start > 5:
            sensor_values.update({'exit':True})
            break
        sys.stdout.write('\r{}'.format(sensor_values))
        time.sleep(0.05)

if __name__ == '__main__':
    mgr = multiprocessing.Manager()
    sensor_values = mgr.dict()
    sensor_values.update({'exit':False})

    p1 = multiprocessing.Process(target=rov, args=(sensor_values,))
    p2 = multiprocessing.Process(target=reader, args=(sensor_values,))
    processes = [p1, p2]

    start = time.time()

    for p in processes:
        p.start()

    for p in processes:
        p.join()