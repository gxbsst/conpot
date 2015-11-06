# coding=utf-8

import socket
import struct
import binascii
import logging
import sys
import time
import threading


logger = logging.getLogger(__name__)
logger.level = logging.INFO
formatter = logging.Formatter('LINE %(lineno)-4d  %(levelname)-8s %(message)s', '%m-%d %H:%M')
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

CHECK_SUM_FMT = '<B'
SEND_ORDER_FMT = '<HI12H'
RECEIVE_ORDER_FMT = '<HI2HB'

# 0x19, 0x27, 0x01, 0x00, 0xff, 0xff, 0xff, 0xff, 0x00, 0x00, 0x00

# s = '\x19\x27\x01\x00\xff\xff\xff\xff\x00\x00\x00'
# header, order_no, oder_step, state, checksum = struct.unpack(RECE_ORDER_FMT, s)
# print header, order_no, oder_step, state, checksum

# _SEND_ORDER_FMT = '<HI12HB'
# s = '\x13\x27\x01\x00\x00\x00\x01\x00\xFF\xFF\xFF\xFF\x01\x00\xFF\x00\xFF\xFF\x00\x00\x04\x00\x05\x00\xE5\x70\x07\x00\xE4\x70\xEF'
# print struct.unpack(_SEND_ORDER_FMT, s)
#
# print sum(bytearray('\x13\x27\x01\x00\x00\x00\x01\x00\xFF\xFF\xFF\xFF\x01\x00\xFF\x00\xFF\xFF\x00\x00\x04\x00\x05\x00\xE5\x70\x07\x00\xE4\x70')) & 0xFF
#
# print binascii.hexlify(struct.pack(CHECK_SUM_FMT, 239))


DEFAULT_HOST = '192.168.1.188'
DEFAULT_PORT = 90002


class MMIS(object):
    def __init__(self, template, template_directory, args):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = DEFAULT_HOST
        self.port = DEFAULT_PORT
        self.connected = False
        self.closed = False

    def connect(self):
        # Connect the socket to the port where the server is listening
        server_address = (self.host, self.port)
        logger.info('connecting to %s port %s' % server_address)
        self.sock.connect(server_address)
        self.connected = True

    @staticmethod
    def checksum(data):
        return struct.pack(CHECK_SUM_FMT, sum(bytearray(data)) & 0xFF)

    def send_order(self, order_no, source_site, target_site):
        data = struct.pack(SEND_ORDER_FMT, 10003, order_no, 0, 0, 0, 1, 255, 0, 0, 4, source_site, 0, target_site, 0)
        data += MMIS.checksum(data)
        logger.info('sending "%s"' % binascii.hexlify(data))
        self.sock.sendall(data)

    def start(self, host, port):
        self.host = host
        self.port = port
        while 1:
            try:
                if self.closed:
                    break
                if not self.connected:
                    self.connect()
                receive_msg = self.sock.recv(11)
                logger.info('received "%s"' % binascii.hexlify(receive_msg))
                header, order_no, oder_step, state, checksum = struct.unpack(RECEIVE_ORDER_FMT, receive_msg)
                logger.info((header, order_no, oder_step, state, checksum))
                if header == 10003:
                    logger.info('订单已确认，订单号: ' + order_no)
                elif header == 10005:
                    logger.info('订单已完成，订单号: ' + order_no)
            except socket.error, e:
                logger.error('Error because: %s' % e)
                self.connected = False

            time.sleep(1)

    def stop(self):
        logger.info('closing socket')
        self.closed = True
        self.sock.close()


mmis = MMIS(None, None, None)
threading.Thread(target=mmis.start, args=('192.168.1.100', 3000)).start()
while 1:
    if mmis.connected:
        mmis.send_order(1, 5, 11)
        break
    time.sleep(1.1)