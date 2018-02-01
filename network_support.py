import subprocess
import socket
from concurrent.futures import ThreadPoolExecutor

STANDARD_PORTS = ['eth0', 'lo', 'wlan0']

def get_port_dict():
    port_dict = {}
    proc = subprocess.Popen('ifconfig', stdout=subprocess.PIPE)
    blocks = proc.stdout.read().split(b'\n\n')
    for port, block in zip(STANDARD_PORTS, blocks):
        lines = block.split(b'\n')
        for line in lines:
            parts = line.decode().replace('  ', ' ').strip().split(' ')
            if parts[0] == 'inet':
                if port in ['eth0', 'wlan0']:
                    port_dict.update({port: {'inet': parts[1][5:],
                                             'netmask': parts[3][5:]}})
                break
            else:
                port_dict.update({port: None})
    return port_dict


def check_ip(ip, port=1060):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        print('testing: {}'.format(ip))
        sock.connect((ip, port))
    except socket.error:
        return None
    print('connected to {}'.format(ip))
    return ip


def possible_ips(hostname, netmask):
    masks = [int(val) == 0 for val in netmask.split('.')]
    ips = hostname.split('.')
    if masks[3]:
        for last in range(0, 256):
            if masks[2]:
                for third in range(0, 256):
                    if masks[1]:
                        for second in range(0, 256):
                            yield ('{}.{}.{}.{}'
                                   .format(ips[0], second, third, last))
                    yield ('{}.{}.{}.{}'
                           .format(ips[0], ips[1], third, last))
            yield ('{}.{}.{}.{}'
                   .format(ips[0], ips[1], ips[2], last))
    else:
        yield hostname


def find_server(port):
    ports = get_port_dict()
    if ports['eth0']:
        ips_to_check = possible_ips(hostname=ports['eth0']['inet'],
                                    netmask=ports['eth0']['netmask'])
    elif ports['wlan0']:
        print(ports['wlan0']['inet']+ports['wlan0']['netmask'])
        ips_to_check = possible_ips(hostname=ports['wlan0']['inet'],
                                    netmask=ports['wlan0']['netmask'])
    else:
        raise(ConnectionAbortedError,
              'Not possible to connect, not connected to ethernet or WiFi.')

    ## Start finding the server
    pool = ThreadPoolExecutor(max_workers=50)
    results = list(pool.map(check_ip, ips_to_check))
    print(len(results))
    # for ip in ips_to_check:
    #     thread = Thread(target=check_ip, args=(ip,port,))
    #     thread.start()
    #     threads.append(thread)
    #     if threading.active_count() >= 100:
    #         for thread in threads:
    #             thread.join()
    # for thread in threads:
    #     thread.join()