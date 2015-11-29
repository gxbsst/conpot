# coding=utf-8

from gevent.lock import RLock
import logging
import socket
import time
from struct import pack, unpack
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
    def __init__(self, point_id, address, count=1, encoding='none', endian='Auto', readonly=False, condition=None, state=None):
        self.point_id = point_id
        self.address = address
        self.count = count
        self.encoding = encoding
        self.endian = endian
        self.slave_id = 1
        self.readonly = readonly
        self.condition = condition
        self.state = state
        self.custom_decoder = None

    def get_read_value(self, value):
        if self.state:
            return self.state
        return value


class MMaster(object):
    def __init__(self, device_node):
        self.connected = False
        self.closed = False
        self.modbus_client = None
        self.slaves = []
        self.point_dict = {}
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
                    condition = None
                    state = None
                    readonly = False
                    if 'readonly' in point_node.attrib:
                        readonly = eval(point_node.attrib['readonly'])
                    if 'condition' in point_node.attrib:
                        condition = point_node.attrib['condition']
                    if 'state' in point_node.attrib:
                        state = point_node.attrib['state']
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
                    custom_decoder_nodes = point_node.xpath('./custom_decoder')
                    if custom_decoder_nodes is not None and len(custom_decoder_nodes) > 0:
                        custom_decoder = custom_decoder_nodes[0].text
                        point.custom_decoder = custom_decoder
                    point.slave_id = slave.slave_id
                    point.readonly = readonly
                    point.condition = condition
                    point.state = state
                    self.point_dict[point_id] = point
                    block.points.append(point)

    def write_coils(self, key):
        point = self.point_dict.get(key[2:])
        if point:
            value = conpot_core.get_databus().get_value(key)
            with lock:
                return self.modbus_client.write_coil(point.address, value, unit=point.slave_id)

    def write_registers(self, key):
        point = self.point_dict.get(key[2:])
        if point:
            value = conpot_core.get_databus().get_value(key)
            if not point.encoding == 'none':
                endian = Endian.Auto
                if point.endian == 'Little':
                    endian = Endian.Little
                elif point.endian == 'Big':
                    endian = Endian.Big
                builder = BinaryPayloadBuilder(endian=endian)
                builder_map = {'bits': builder.add_bits,
                               '8unit': builder.add_8bit_uint,
                               '16unit': builder.add_16bit_uint,
                               '32unit': builder.add_32bit_uint,
                               '64unit': builder.add_64bit_uint,
                               '8int': builder.add_8bit_int,
                               '16int': builder.add_16bit_int,
                               '32int': builder.add_32bit_int,
                               '64int': builder.add_64bit_int,
                               '32float': builder.add_32bit_float,
                               '64float': builder.add_64bit_float,
                               'string': builder.add_string}
                builder_map[point.encoding](value)

                payload = [unpack(endian + 'H', x)[0] for x in builder.build()]
                with lock:
                    return self.modbus_client.write_registers(point.address,
                                                              payload,
                                                              unit=point.slave_id)
            else:
                with lock:
                    return self.modbus_client.write_registers(point.address, [value], unit=point.slave_id)

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
                        if not point.readonly:
                            conpot_core.get_databus().observe_value('w ' + point.point_id,
                                                                    lambda key: self.write_coils(key))
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
                        if not point.readonly:
                            conpot_core.get_databus().observe_value('w ' + point.point_id,
                                                                    lambda key: self.write_registers(key))
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
                                if not point.encoding == 'none' and not point.encoding == 'custom':
                                    endian = Endian.Auto
                                    if point.endian == 'Little':
                                        endian = Endian.Little
                                    elif point.endian == 'Big':
                                        endian = Endian.Big
                                    payload = ''.join(pack(endian + 'H', x) for x in value)
                                    decoder = BinaryPayloadDecoder(payload, endian)
                                    encoding_map = {'bits': decoder.decode_bits,
                                                    '8unit': decoder.decode_8bit_uint,
                                                    '16unit': decoder.decode_16bit_uint,
                                                    '32unit': decoder.decode_32bit_uint,
                                                    '64unit': decoder.decode_64bit_uint,
                                                    '8int': decoder.decode_8bit_int,
                                                    '16int': decoder.decode_16bit_int,
                                                    '32int': decoder.decode_32bit_int,
                                                    '64int': decoder.decode_64bit_int,
                                                    '32float': decoder.decode_32bit_float,
                                                    '64float': decoder.decode_64bit_float,
                                                    'string': decoder.decode_string}
                                    value = encoding_map[point.encoding]()
                                elif point.encoding == 'custom' and point.custom_decoder:
                                    decode = eval("lambda value: " + point.custom_decoder)
                                    value = decode(value)

                            if point.condition:
                                if point.condition[0] == '=':
                                    if str(value) == point.condition[1:]:
                                        conpot_core.get_databus().set_value('r ' + point.point_id,
                                                                            point.get_read_value(value))
                                elif point.condition[0] == '!':
                                    if not str(value) == point.condition[1:]:
                                        conpot_core.get_databus().set_value('r ' + point.point_id,
                                                                            point.get_read_value(value))
                                elif point.condition[0] == '>':
                                    if str(value) > point.condition[1:]:
                                        conpot_core.get_databus().set_value('r ' + point.point_id,
                                                                            point.get_read_value(value))
                                elif point.condition[0] == '<':
                                    if str(value) < point.condition[1:]:
                                        conpot_core.get_databus().set_value('r ' + point.point_id,
                                                                            point.get_read_value(value))
                            else:
                                conpot_core.get_databus().set_value('r ' + point.point_id,
                                                                    point.get_read_value(value))
            except ConnectionException, e:
                logger.error('Error because: %s' % e)
                self.connected = False
            time.sleep(update_period)

    def stop(self):
        self.closed = True
        self.modbus_client.close()