#!/usr/bin/env python3
# Foundations of Python Network Programming, Third Edition
# https://github.com/brandon-rhodes/fopnp/blob/m/py3/chapter02/udp_local.py
# UDP client and server on localhost

import argparse, socket, platform, sys
import io
import struct
import time
if platform.system() == 'Linux':
    import picamera
import pygame
screen_size = width, height = 640, 480
from PIL import Image


class SplitFrames(object):
    def __init__(self, connection):
        self.connection = connection
        self.stream = io.BytesIO()
        self.count = 0

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # Start of new frame; send the old one's length
            # then the data
            size = self.stream.tell()
            if size > 0:
                self.connection.write(struct.pack('<L', size))
                self.connection.flush()
                self.stream.seek(0)
                self.connection.write(self.stream.read(size))
                self.count += 1
                self.stream.seek(0)
        self.stream.write(buf)


def server(interface, port):
    pygame.init()
    screen = pygame.display.set_mode(screen_size)
    # snapshot = pygame.image.load("flower.jpg")

    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((interface, port))
    server_socket.listen(0)
    print('Listening at', server_socket.getsockname())

    # Accept a single connection and make a file-like object out of it
    connection = server_socket.accept()[0].makefile('rb')
    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: sys.exit()

            # Read the length of the image as a 32-bit unsigned int. If the
            # length is zero, quit the loop
            image_len = \
                struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
            if not image_len:
                break
            # Construct a stream to hold the image data and read the image
            # data from the connection
            image_stream = io.BytesIO()
            image_stream.write(connection.read(image_len))
            # Rewind the stream, open it as an image with PIL and do some
            # processing on it

            data = Image.open(image_stream).tobytes()
            snapshot = pygame.image.fromstring(data, screen_size, 'RGB')
            # snapshot = pygame.image.frombuffer(image_stream.read(),
            #                                    screen_size, 'RGB')
            # snapshot = pygame.image.load(image_stream)
            screen.blit(snapshot, (0,0))
            pygame.display.flip()
            image_stream.seek(0)
    finally:
        connection.close()
        server_socket.close()


def client(host, port):
    client_socket = socket.socket()
    client_socket.connect((host, port))
    print('Client has been assigned socket name', client_socket.getsockname())
    connection = client_socket.makefile('wb')
    try:
        output = SplitFrames(connection)
        with picamera.PiCamera(resolution='VGA', framerate=30) as camera:
            time.sleep(2)
            start = time.time()
            camera.start_recording(output, format='mjpeg')
            camera.wait_recording(10)
            camera.stop_recording()
            # Write the terminating 0-length to the connection to let the
            # server know we're done
            connection.write(struct.pack('<L', 0))
    finally:
        connection.close()
        client_socket.close()
        finish = time.time()
    print('Sent %d images in %d seconds at %.2ffps' % (
        output.count, finish - start, output.count / (finish - start)))


if __name__ == '__main__':
    choices = {'client': client, 'server': server}
    parser = argparse.ArgumentParser(description='Stream video from rpi cam')
    parser.add_argument('role', choices=choices, help='which role to play')
    parser.add_argument('host', help='interface the server listens at;'
                        ' host the client sends to')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060,
                        help='TCP port (default 1060)')
    args = parser.parse_args()
    function = choices[args.role]
    function(args.host, args.p)
