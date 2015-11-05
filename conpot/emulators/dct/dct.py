# coding=utf-8

import socket
import binascii
import logging
import errno
import time
from enum import Enum
import sys

logger = logging.getLogger(__name__)
# stream_handler = logging.StreamHandler(sys.stderr)
# logger.addHandler(stream_handler)

# 发送命令串
READ_STATUS_MSG = '\x01\x03\x00\x1B\x00\x05'

START_1_2_MSG = '\x01\x10\x00\x14\x00\x05\x0A\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00'
PAUSE_1_2_MSG = '\x01\x10\x00\x14\x00\x05\x0A\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00'
REST_1_2_MSG = '\x01\x10\x00\x14\x00\x05\x0A\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00'

START_1_3_MSG = '\x01\x10\x00\x14\x00\x05\x0A\x00\x09\x00\x00\x00\x00\x00\x00\x00\x00'
PAUSE_1_3_MSG = '\x01\x10\x00\x14\x00\x05\x0A\x00\x0A\x00\x00\x00\x00\x00\x00\x00\x00'
REST_1_3_MSG = '\x01\x10\x00\x14\x00\x05\x0A\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00'

REST_ALL = '\x01\x10\x00\x14\x00\x05\x0A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'


# 基本状态
class State(Enum):
    # 等待开始状态
    waiting = 0
    # 停止状态
    stopped = 1
    # 暂停状态
    halt = 2
    # 运行状态
    running = 4
    # 故障状态
    fault = 8
    # 维修状态
    repair = 16


# 载重状态
class LoadState(Enum):
    no_load = 1
    full_load = 2


SITE_1_FLAG = 32
SITE_2_FLAG = 64
SITE_3_FLAG = 128


class RGVError(Exception):
    def __init__(self, index, error_no, message):
        self.index = index
        self.error_no = error_no
        self.message = message

    def __str__(self):
        return 'RGVError - [error: ' + self.message + ']'


ERRORS = (
    RGVError(6, 1, "台车通信异常1"),
    RGVError(6, 2, "台车通信异常2"),
    RGVError(6, 4, "子台车电机超时"),
    RGVError(6, 8, "母台车电机超时"),
    RGVError(6, 16, "平台升降超时"),
    RGVError(6, 32, "母台车定位销超时"),
    RGVError(6, 64, "子台车定位销超时"),
    RGVError(6, 128, "平台工件检测异常"),

    RGVError(5, 1, "台车编码器异常"),
    RGVError(5, 2, "子车变频器报警"),
    RGVError(5, 4, "母车变频器报警"),
    RGVError(5, 8, "母车定位销热继"),
    RGVError(5, 16, "子车液压站热继"),
    RGVError(5, 32, "操作盒急停"),
    RGVError(5, 64, "台车面板急停"),

    RGVError(8, 1, "系统通信异常1"),
    RGVError(8, 2, "系统通信异常2"),
    RGVError(8, 4, "地面正转异常"),
    RGVError(8, 8, "地面反转异常"),
    RGVError(8, 16, "地面回转热继"),
    RGVError(8, 32, "系统面板急停")
)

DEFAULT_HOST = '192.168.1.188'
DEFAULT_PORT = 90002


class DCT(object):
    def __init__(self, template, template_directory, args):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = DEFAULT_HOST
        self.port = DEFAULT_PORT
        self.current_site = 1
        self.source_site = 1
        self.target_site = 1
        self.state = State.waiting
        self.load_state = LoadState.no_load
        self.errors = set()
        self.connected = False
        self.closed = False

    def __str__(self):
        return 'DCT - [current_site: ' + str(self.current_site) + ', load_state: ' + str(
            self.load_state) + ', state: ' + str(self.state) \
               + ', errors: ' + str(self.errors) + ']'

    def connect(self):
        # Connect the socket to the port where the server is listening
        server_address = (self.host, self.port)
        logger.info('connecting to %s port %s' % server_address)
        self.sock.connect(server_address)
        self.sock.sendall(READ_STATUS_MSG)
        self.connected = True

    def execute_msg(self, reset_msg, order_msg):
        # 重置
        logger.info('sending "%s"' % binascii.hexlify(reset_msg))
        self.sock.sendall(reset_msg)

        # 收到信息
        receive_msg = self.sock.recv(6)
        logger.info('received "%s"' % binascii.hexlify(receive_msg))

        # 执行启动命令
        logger.info('sending "%s"' % binascii.hexlify(order_msg))
        self.sock.sendall(order_msg)

        # 收取信息
        receive_msg = self.sock.recv(6)
        logger.info('received "%s"' % binascii.hexlify(receive_msg))

    def go(self, source_site=1, target_site=1):
        """
        指定目标站点启动
        """
        try:
            # 首先获取小车状态
            self.get_rgv_state()
            # 如果小车不处于停止状态直接返回
            if (not self.state == State.stopped) and (not self.state == State.halt):
                return
            if (source_site == 1 and target_site == 2) or (source_site == 2 and target_site == 1):
                self.execute_msg(REST_1_2_MSG, START_1_2_MSG)
            elif (source_site == 1 and target_site == 3) or (source_site == 3 and target_site == 1):
                self.execute_msg(REST_1_3_MSG, START_1_3_MSG)
            else:
                return
            self.source_site = source_site
            self.target_site = target_site
        except socket.error, e:
            if e.errno == errno.ECONNRESET:
                # Handle disconnection -- close & reopen socket etc.
                logging.exception(e)
                self.connected = False
            else:
                # Other error
                raise

    def pause(self):
        """
        暂停小车
        """
        try:
            # 首先获取小车状态
            self.get_rgv_state()
            # 如果小车不处于停止状态直接返回
            if not self.state == State.running:
                return
            if (self.source_site == 1 and self.target_site == 2) or (self.source_site == 2 and self.target_site == 1):
                self.execute_msg(REST_1_2_MSG, PAUSE_1_2_MSG)
            elif (self.source_site == 1 and self.target_site == 3) or (self.source_site == 3 and self.target_site == 1):
                self.execute_msg(REST_1_3_MSG, PAUSE_1_3_MSG)
            else:
                return
        except socket.error, e:
            if e.errno == errno.ECONNRESET:
                # Handle disconnection -- close & reopen socket etc.
                logging.exception(e)
                self.connected = False
            else:
                # Other error
                raise

    def unpack_errors(self, msg_bytes):
        for err in ERRORS:
            if err.index < len(msg_bytes) and msg_bytes[err.index] & err.error_no == err.error_no:
                self.errors.add(err)

    def unpack_state(self, msg_bytes):
        if msg_bytes[3] & LoadState.no_load.value == LoadState.no_load.value:
            self.load_state = LoadState.no_load
        elif msg_bytes[3] & LoadState.full_load.value == LoadState.full_load.value:
            self.load_state = LoadState.full_load

        if msg_bytes[4] & State.stopped.value == State.stopped.value:
            self.state = State.stopped
        elif msg_bytes[4] & State.halt.value == State.halt.value:
            self.state = State.halt
        elif msg_bytes[4] & State.running.value == State.running.value:
            self.state = State.running
        elif msg_bytes[4] & State.fault.value == State.fault.value:
            self.state = State.fault
        elif msg_bytes[4] & State.repair.value == State.repair.value:
            self.state = State.repair
        else:
            self.state = State.waiting

        if msg_bytes[4] & SITE_1_FLAG == SITE_1_FLAG:
            self.current_site = 1
        elif msg_bytes[4] & SITE_2_FLAG == SITE_2_FLAG:
            self.current_site = 2
        elif msg_bytes[4] & SITE_3_FLAG == SITE_3_FLAG:
            self.current_site = 3

        if self.state == State.halt:
            self.unpack_errors(msg_bytes)
        elif len(self.errors) > 0:
            self.errors.clear()

    def get_rgv_state(self):
        logger.info('sending "%s"' % binascii.hexlify(READ_STATUS_MSG))
        self.sock.sendall(READ_STATUS_MSG)
        # Look for the response
        receive_msg = self.sock.recv(13)
        logger.info('received "%s"' % binascii.hexlify(receive_msg))
        self.unpack_state(bytearray(receive_msg))

    def start(self, host, port):
        self.host = host
        self.port = port
        while 1:
            try:
                if self.closed:
                    break
                if not self.connected:
                    self.connect()
                self.get_rgv_state()
                time.sleep(1)
            except socket.error, e:
                if e.errno == errno.ECONNRESET:
                    # Handle disconnection -- close & reopen socket etc.
                    logging.exception(e)
                    self.connected = False
                else:
                    # Other error
                    logger.error('Error because: %s' % e)
                    break

    def stop(self):
        logger.info('closing socket')
        self.closed = True
        self.sock.close()

# while 1:
# order = sys.stdin.readline().rstrip()
#     if order == 's':
#         threading.Thread(target=dct.start()).start()
#     elif order == 'p':
#         dct.pause()
#     elif order.startswith('g'):
#         sites = order.split(' ', 1)
#         dct.go(int(sites[1]))
#     elif order == 'w':
#         print dct
