# -*- coding:utf-8 -*-
import socket
import binascii
import logging
import errno
import time
from enum import Enum
import sys
import conpot.core as conpot_core
from gevent.lock import RLock


lock = RLock()

logger = logging.getLogger(__name__)


# Send Message
READ_STATUS_MSG = '\x01\x03\x00\x1B\x00\x05'


class SysState(Enum):
    # 系统异常
    sys_error = 1


class RobotState(Enum):
    # 机器人异常
    robot_error = 2
    # 机器人报警
    robot_alarm = 4


class WorkState(Enum):
    # 示教中
    teaching = 8
    # 再生中
    repeating = 16
    # 电弧ON
    electric_arc = 32
    # 再生暂停中
    repeat_halting = 64
    # 再生正常结束
    repeating_end_normally = 128


class DriveState(Enum):
    # 伺服ON许可
    servo = 1
    # 外部启动许可
    external_start = 2


ERRORS = {1: u"系统异常", 2: u"机器人异常", 4: u"机器人报警"}

DEFAULT_HOST = '192.168.1.188'
DEFAULT_PORT = 9003

TIME_REPEAT = []
TIME_HALT_OR_END = []


class WeldRobot(object):
    def __init__(self, template, template_directory, args):
        # Create a TCP/IP socket
        self.sock = None
        self.host = DEFAULT_HOST
        self.port = DEFAULT_PORT
        self.state = "Waiting"
        self.connected = False
        self.closed = False
        self.servo_ON = False
        self.isWelding = False
        self.errors = set()
        self.hasErrors = False
        self.repeat_time = 0

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
        self.sock.sendall(READ_STATUS_MSG)
        self.connected = True

    def unpack_state(self, msg_bytes):
        if len(msg_bytes) != 13:    # 未正确返回数据，直接返回
            return
        self.errors.clear()   # 先清除之前的错误信息
        # 错误信息
        if msg_bytes[4] & SysState.sys_error.value == SysState.sys_error.value:
            self.errors.add(ERRORS[SysState.sys_error.value])
        if msg_bytes[4] & RobotState.robot_error.value == RobotState.robot_error.value:
            self.errors.add(ERRORS[RobotState.robot_error.value])
        if msg_bytes[4] & RobotState.robot_alarm.value == RobotState.robot_alarm.value:
            self.errors.add(ERRORS[RobotState.robot_alarm.value])
        # print 'errors:', self.errors

        if len(self.errors):
            self.hasErrors = True
        else:
            self.hasErrors = False

        conpot_core.get_databus().set_value('r ns=1;s=KYWeldRobot.hasErrors', self.hasErrors)

        # 伺服驱动ON，操作可进行
        if msg_bytes[3] & DriveState.servo.value == DriveState.servo.value:
            self.servo_ON = True
        else:
            self.servo_ON = False
        # print 'servo ON? : ', self.servo_ON

        conpot_core.get_databus().set_value('r ns=1;s=KYWeldRobot.servo_ON', self.servo_ON)

        # 焊接机器人工作状态(手动示教/自动再生)
        if msg_bytes[4] & WorkState.teaching.value == WorkState.teaching.value:
            self.state = WorkState.teaching
        elif msg_bytes[4] & WorkState.repeating.value == WorkState.repeating.value:
            self.state = WorkState.repeating
            TIME_REPEAT.append(time.time())
            if msg_bytes[4] & WorkState.repeat_halting.value == WorkState.repeat_halting.value:
                self.state = WorkState.repeat_halting
                TIME_HALT_OR_END.append(time.time())
        elif msg_bytes[4] & WorkState.repeating_end_normally.value == WorkState.repeating_end_normally.value:
            self.state = WorkState.repeating_end_normally
            TIME_HALT_OR_END.append(time.time())
        # print 'KYWeldRobot working state:', self.state.name

        conpot_core.get_databus().set_value('r ns=1;s=KYWeldRobot.State', self.state.name)

        # 是否正在进行焊接
        if msg_bytes[4] & WorkState.electric_arc.value == WorkState.electric_arc.value:
            self.isWelding = True
        else:
            self.isWelding = False
        # print 'Welding? : ', self.isWelding

        conpot_core.get_databus().set_value('r ns=1;s=KYWeldRobot.isWelding', self.isWelding)

    def get_weldrobot_state(self):
        with lock:
            logger.debug('sending "%s"' % binascii.hexlify(READ_STATUS_MSG))
            self.sock.sendall(READ_STATUS_MSG)
            # Look for the response
            receive_msg = self.sock.recv(13)
            print binascii.hexlify(receive_msg)
            logger.debug('received "%s"' % binascii.hexlify(receive_msg))
            self.unpack_state(bytearray(receive_msg))
            self.repeat_time = sum(TIME_HALT_OR_END) - sum(TIME_REPEAT)
            del TIME_HALT_OR_END[:]
            del TIME_REPEAT[:]
            # conpot_core.get_databus().set_value('r ns=1;s=KYWeldRobot.repeat_time', self.repeat_time)

    def start(self, host, port):
        self.host = host
        self.port = port
        while 1:
            try:
                if self.closed:
                    break
                if not self.connected:
                    self.connect()
                self.get_weldrobot_state()
            except socket.error, e:
                logger.error('Error because: %s' % e)
                self.connected = False

            time.sleep(1)

    def stop(self):
        logger.info('closing socket')
        self.closed = True
        self.sock.close()


if __name__ == '__main__':
    KYWeldRobot = WeldRobot()
    KYWeldRobot.connect()
    KYWeldRobot.start(DEFAULT_HOST, DEFAULT_PORT)
    KYWeldRobot.stop()

    # KYWeldRobot.unpack_state()
