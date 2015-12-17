# coding=utf-8

import socket
import struct
import binascii
import logging
import sys
import time
import threading
import conpot.core as conpot_core


logger = logging.getLogger(__name__)
logger.level = logging.INFO
formatter = logging.Formatter('LINE %(lineno)-4d  %(levelname)-8s %(message)s', '%m-%d %H:%M')
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

HEADER_FMT = '<H'
CHECK_SUM_FMT = '<B'
SEND_ORDER_FMT = '<HI12H'
RECEIVE_ORDER_FMT = '<HI2HB'
CONFIRM_ORDER_FMT = '<HIH'

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

# s = '\x13\x27\x01\x00\x00\x00\x00\x00\x01\x00\x3c'
# print struct.unpack(RECEIVE_ORDER_FMT, s)

DEFAULT_HOST = '192.168.1.100'
DEFAULT_PORT = 3000


class MMIS(object):
    def __init__(self, template, template_directory, args):
        self.sock = None
        self.host = DEFAULT_HOST
        self.port = DEFAULT_PORT
        self.connected = False
        self.closed = False

    def connect(self):
        if self.sock and not self.connected:
            # 关闭失败的连接
            self.sock.close()
            # 等待重连
            time.sleep(1)
        # Connect the socket to the port where the server is listening
        server_address = (self.host, self.port)
        logger.info('connecting to %s port %s' % server_address)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(server_address)
        self.connected = True

        # 绑定callback
        conpot_core.get_databus().observe_value('w ns=1;s=SSAgv.SendOrder', lambda key: self.bind_send_order(key))

    @staticmethod
    def checksum(data):
        return struct.pack(CHECK_SUM_FMT, sum(bytearray(data)) & 0xFF)

    def bind_send_order(self, key):
        order_no, source_site, target_site = conpot_core.get_databus().get_value(key)
        return self.send_order(order_no, source_site, target_site)

    def send_order(self, order_no, source_site, target_site):
        try:
            data = struct.pack(SEND_ORDER_FMT, 10003, order_no, 0, 0, 0, 1, 255, 0, 0, 4, source_site, 0, target_site, 0)
            data += MMIS.checksum(data)
            self.sock.sendall(data)
            logger.info('sending "%s"' % binascii.hexlify(data))
            logger.info('发送订单，订单号: ' + str(order_no) + ' 取货点: ' + str(source_site) + ' 送货点: ' + str(target_site))
        except socket.error, e:
            return False
        return True

    def confirm_order(self, order_no):
        data = struct.pack(CONFIRM_ORDER_FMT, 10005, order_no, 0xFFFF)
        data += MMIS.checksum(data)
        self.sock.sendall(data)
        logger.info('sending "%s"' % binascii.hexlify(data))
        logger.info('确认订单完成: ' + str(order_no))

    def recv_msg(self, header_1_msg, header_1_byte, header_2_byte):
        if header_1_msg == header_1_byte:
            header_2_msg = self.sock.recv(1)
            if header_2_msg == header_2_byte:
                body_msg = self.sock.recv(8)
                checksum_msg = self.sock.recv(1)
                if MMIS.checksum(header_1_msg + header_2_msg + body_msg) == checksum_msg:
                    all_msg = header_1_msg + header_2_msg + body_msg + checksum_msg
                    logger.info('received "%s"' % binascii.hexlify(all_msg))
                    return struct.unpack(RECEIVE_ORDER_FMT, all_msg)
        return None

    def start(self, host, port):
        self.host = host
        self.port = port
        while 1:
            try:
                if self.closed:
                    break
                if not self.connected:
                    self.connect()

                header_1_msg = self.sock.recv(1)
                recv_msg = self.recv_msg(header_1_msg, '\x13', '\x27')
                if recv_msg:
                    print "***************订单已确认***************************"
                    header, order_no, oder_step, state, checksum = recv_msg
                    logger.info('订单已确认，订单号: ' + str(order_no))
                    conpot_core.get_databus().set_value('r ns=1;s=SSAgv.ConfirmedEvent', order_no, forced=True)
                    continue
                recv_msg = self.recv_msg(header_1_msg, '\x15', '\x27')
                if recv_msg:
                    print "***************订单已完成***************************"
                    header, order_no, oder_step, vno, checksum = recv_msg
                    logger.info('订单已完成，订单号: ' + str(order_no))
                    conpot_core.get_databus().set_value('r ns=1;s=SSAgv.CompletedEvent', order_no, forced=True)
                    self.confirm_order(order_no)
            except socket.error, e:
                logger.error('Error because: %s' % e)
                self.connected = False

    def stop(self):
        logger.info('closing socket')
        self.closed = True
        self.sock.close()


# mmis = MMIS(None, None, None)
# threading.Thread(target=mmis.start, args=('192.168.1.100', 3000)).start()
# while 1:
#     if mmis.connected:
#         mmis.send_order(2, 11, 5)
#         break
#     time.sleep(1.1)