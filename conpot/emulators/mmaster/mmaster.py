# coding=utf-8

from gevent.lock import RLock
import logging
import socket
import time
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.register_read_message import ReadHoldingRegistersResponse
from pymodbus.bit_read_message import ReadCoilsResponse
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
import conpot.core as conpot_core
from pymodbus.exceptions import ConnectionException

logger = logging.getLogger(__name__)
# logger.level = logging.INFO
# stream_handler = logging.StreamHandler(sys.stderr)
# logger.addHandler(stream_handler)

lock = RLock()


class Slave(object):
    def __init__(self, slave_id):
        self.slave_id = slave_id
        self.blocks = []


class Block(object):
    def __init__(self, range_type, starting_address, size):
        self.range_type = range_type
        self.starting_address = starting_address
        self.size = size
        self.points = []


class Point(object):
    def __init__(self, point_id, address, count=1, encoding='none', endian='Auto'):
        self.point_id = point_id
        self.address = address
        self.count = count
        self.encoding = encoding
        self.endian = endian


class MMaster(object):
    def __init__(self, device_node):
        self.connected = False
        self.closed = False
        self.modbus_client = None
        self.slaves = []
        self.executions = []
        self.parse(device_node)

    def parse(self, device_node):
        """
        通过device节点解析xml中slave中具体数据
        """
        slave_nodes = device_node.xpath('./slave')
        for slave_node in slave_nodes:
            slave_id = int(slave_node.attrib['id'])
            slave = Slave(slave_id)
            self.slaves.append(slave)
            block_nodes = slave_node.xpath('./block')
            for block_node in block_nodes:
                range_type = block_node.xpath('./type')[0].text
                starting_address = int(block_node.xpath('./starting_address')[0].text)
                size = int(block_node.xpath('./size')[0].text)
                block = Block(range_type, starting_address, size)
                slave.blocks.append(block)
                point_nodes = block_node.xpath('point')
                for point_node in point_nodes:
                    point_id = point_node.attrib['id']
                    address = point_node.xpath('./address')[0].text
                    point = Point(point_id, int(address))
                    count_nodes = point_node.xpath('./count')
                    if count_nodes is not None and len(count_nodes) > 0:
                        point.count = int(count_nodes[0].text)
                    encoding_nodes = point_node.xpath('./encoding')
                    if encoding_nodes is not None and len(encoding_nodes) > 0:
                        point.encoding = encoding_nodes[0].text
                    endian_nodes = point_node.xpath('./endian')
                    if endian_nodes is not None and len(endian_nodes) > 0:
                        endian = endian_nodes[0].text
                        point.endian = endian
                    block.points.append(point)

    def write_coils(self, address, value, unit=1):
        with lock:
            return self.modbus_client.write_coils(address, value, unit=unit)

    def write_registers(self, point, address, value, unit=1):
        if not point.encoding == 'none':
            endian = Endian.Auto
            if point.endian == 'Little':
                endian = Endian.Little
            elif point.endian == 'Big':
                endian = Endian.Big
            builder = BinaryPayloadBuilder(endian=endian)
            if point.encoding == 'bits':
                builder.add_bits(value)
            elif point.encoding == '8int':
                builder.add_8bit_int(value)
            elif point.encoding == '16uint':
                builder.add_16bit_uint(value)
            elif point.encoding == 'float':
                builder.add_32bit_float(value)
            elif point.encoding == 'string':
                builder.add_string(value)
            with lock:
                return self.modbus_client.write_registers(address, builder.build(), unit=unit, skip_encode=True)
        else:
            with lock:
                return self.modbus_client.write_registers(address, [value], unit=unit)

    def read_coils(self, address, size, unit=1):
        with lock:
            return self.modbus_client.read_coils(address, size, unit=unit)

    def read_discrete_inputs(self, address, size, unit=1):
        with lock:
            return self.modbus_client.read_discrete_inputs(address, size, unit=unit)

    def read_holding_registers(self, address, size, unit=1):
        with lock:
            return self.modbus_client.read_holding_registers(address, size, unit=unit)

    def read_input_registers(self, address, size, unit=1):
        with lock:
            return self.modbus_client.read_input_registers(address, size, unit=unit)

    def iterate_blocks(self):
        """
        遍历所有的block，缓存执行序列，并订阅点值的写入
        """
        for slave in self.slaves:
            for block in slave.blocks:
                if block.range_type == 'COILS':
                    self.executions.append((self.read_coils,
                                            block.starting_address,
                                            block.size,
                                            slave.slave_id,
                                            block.points))
                    for point in block.points:
                        conpot_core.get_databus().observe_value('w ' + point.point_id,
                                                                lambda key: self.write_coils(
                                                                    point.address,
                                                                    conpot_core.get_databus().get_value(key),
                                                                    unit=slave.slave_id))
                elif block.range_type == 'DISCRETE_INPUTS':
                    self.executions.append((self.read_discrete_inputs,
                                            block.starting_address,
                                            block.size,
                                            slave.slave_id,
                                            block.points))
                elif block.range_type == 'HOLDING_REGISTERS':
                    self.executions.append((self.read_holding_registers,
                                            block.starting_address,
                                            block.size,
                                            slave.slave_id,
                                            block.points))
                    for point in block.points:
                        conpot_core.get_databus().observe_value('w ' + point.point_id,
                                                                lambda key: self.write_registers(
                                                                    point,
                                                                    point.address,
                                                                    conpot_core.get_databus().get_value(key),
                                                                    unit=slave.slave_id))
                elif block.range_type == 'INPUT_REGISTERS':
                    self.executions.append((self.read_input_registers,
                                            block.starting_address,
                                            block.size,
                                            slave.slave_id,
                                            block.points))

    def connect(self):
        """
        连接MODBUS Slave
        """
        self.modbus_client.connect()
        self.connected = True

    def start(self, host, port, update_period):
        self.modbus_client = ModbusClient(host, port=port)
        self.iterate_blocks()
        while not self.closed:
            try:
                if not self.connected:
                    self.connect()
                for method, starting_address, size, slave_id, points in self.executions:
                    result = method(starting_address, size, unit=slave_id)
                    if result:
                        for point in points:
                            value = None
                            if isinstance(result, ReadCoilsResponse):
                                value = result.bits[point.address - starting_address]
                            elif isinstance(result, ReadHoldingRegistersResponse):
                                start = point.address - starting_address
                                value = result.registers[start:start + point.count]
                                if not point.encoding == 'none':
                                    endian = Endian.Auto
                                    if point.endian == 'Little':
                                        endian = Endian.Little
                                    elif point.endian == 'Big':
                                        endian = Endian.Big
                                    decoder = BinaryPayloadDecoder.fromRegisters(value, endian=endian)
                                    if point.encoding == 'bits':
                                        value = decoder.decode_bits()
                                    elif point.encoding == '8int':
                                        value = decoder.decode_8bit_int()
                                    elif point.encoding == '16uint':
                                        value = decoder.decode_16bit_uint()
                                    elif point.encoding == 'float':
                                        value = decoder.decode_32bit_float()
                                    elif point.encoding == 'string':
                                        value = decoder.decode_string(point.count)

                            conpot_core.get_databus().set_value('r ' + point.point_id, value)
            except ConnectionException, e:
                logger.error('Error because: %s' % e)
                self.connected = False
            time.sleep(update_period)

    def stop(self):
        self.closed = True
        self.modbus_client.close()