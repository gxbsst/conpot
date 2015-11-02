# coding=utf-8

import socket
import struct
import binascii
import logging
import errno
import time
from enum import Enum

logger = logging.getLogger(__name__)

# 发送命令串
READ_STATUS_MSG = '\x01\x03\x00\x1B\x00\x05'

START_1_2_MSG = '\x01\x10\x00\x14\x00\x05\x0A\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00'
PAUSE_1_2_MSG = '\x01\x10\x00\x14\x00\x05\x0A\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00'
REST_1_2_MSG = '\x01\x10\x00\x14\x00\x05\x0A\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00'

START_1_3_MSG = '\x01\x10\x00\x14\x00\x05\x0A\x00\x09\x00\x00\x00\x00\x00\x00\x00\x00'
PAUSE_1_3_MSG = '\x01\x10\x00\x14\x00\x05\x0A\x00\x0A\x00\x00\x00\x00\x00\x00\x00\x00'
REST_1_3_MSG = '\x01\x10\x00\x14\x00\x05\x0A\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00'

REST_ALL = '\x01\x10\x00\x14\x00\x05\x0A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

# 运行状态
State = Enum('State', 'stopped halt running fault repair')
# 载重状态
LoadState = Enum('LState', 'no_load full_load')


class DCT(object):
    def __init__(self, host, port, current_site=1, state=State.stopped, load_state=LoadState.no_load):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the port where the server is listening
        self.server_address = (host, port)
        logger.info('connecting to %s port %s' % self.server_address)
        self.sock.connect(self.server_address)
        self.current_site = current_site
        self.target_site = current_site
        self.state = state
        self.load_state = load_state

    def reconnect(self):
        self.sock.connect(self.server_address)

    def reset(self):
        if (self.current_site == 1 and self.target_site == 2) or (self.current_site == 2 and self.target_site == 1):
            logger.info('sending "%s"' % binascii.hexlify(REST_1_2_MSG))
            self.sock.sendall(REST_1_2_MSG)
        elif (self.current_site == 1 and self.target_site == 3) or (self.current_site == 3 and self.target_site == 1):
            logger.info('sending "%s"' % binascii.hexlify(REST_1_3_MSG))
            self.sock.sendall(REST_1_3_MSG)
        # Look for the response
        receive_msg = self.sock.recv(7)
        logger.info('received "%s"' % binascii.hexlify(receive_msg))

    def go(self, target_site=1):
        # 如果小车不处于停止状态直接返回
        if not self.state == State.stopped:
            return
        try:
            if (self.current_site == 1 and target_site == 2) or (self.current_site == 2 and target_site == 1):
                logger.info('sending "%s"' % binascii.hexlify(START_1_2_MSG))
                self.sock.sendall(START_1_2_MSG)
            elif (self.current_site == 1 and target_site == 3) or (self.current_site == 3 and target_site == 1):
                logger.info('sending "%s"' % binascii.hexlify(START_1_3_MSG))
                self.sock.sendall(PAUSE_1_3_MSG)
            else:
                return
            self.target_site = target_site
            # Look for the response
            receive_msg = self.sock.recv(7)
            logger.info('received "%s"' % binascii.hexlify(receive_msg))
            # Reset
            self.reset()
        except socket.error, e:
            if e.errno == errno.ECONNRESET:
                # Handle disconnection -- close & reopen socket etc.
                logger.info("")
                self.reconnect()
            else:
                # Other error
                raise

    def start(self):
        while 1:
            try:
                logger.info('sending "%s"' % binascii.hexlify(READ_STATUS_MSG))
                self.sock.sendall(READ_STATUS_MSG)
                # Look for the response
                receive_msg = self.sock.recv(7)
                logger.info('received "%s"' % binascii.hexlify(receive_msg))

            except socket.error, e:
                if e.errno == errno.ECONNRESET:
                    # Handle disconnection -- close & reopen socket etc.
                    logger.info("")
                    self.reconnect()
                else:
                    # Other error
                    logger.error('Error because: %s' % e)

            time.sleep(1)

    def stop(self):
        logger.info('closing socket')
        self.sock.close()