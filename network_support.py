import subprocess
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

STANDARD_PORTS = ['eth0', 'lo', 'wlan0']

def sendall_(data, sock):
    length = "{0:#0{1}x}".format(len(data),10).encode()
    sock.sendall(length+data)

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
    if ip is None:
        print('what the heck?')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((ip, port))
    # msg = b'hey there server'
    # print('sending {} MB'.format(len(msg)/1000000))
    # sendall_(msg, sock)
    sock.close()
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
        ips_to_check = possible_ips(hostname=ports['wlan0']['inet'],
                                    netmask=ports['wlan0']['netmask'])
    else:
        raise(ConnectionAbortedError,
              'Not possible to connect, not connected to ethernet or WiFi.')

    with ThreadPoolExecutor(
            max_workers=100) as executor:
        # Start the load operations and mark each future with its URL
        future_to_url = {executor.submit(check_ip, ip): ip for
                         ip in ips_to_check}
        for future in as_completed(future_to_url, timeout=3):
            if future.running():
                print(future)
            try:
                data = future.result(timeout=3)
            except Exception as exc:
                pass
            else:
                print(data)
                break
    return None