from lxml import etree
import logging
import os
import sys
import ast

logger = logging.getLogger(__name__)
stream_handle = logging.StreamHandler(sys.stderr)
logger.addHandler(stream_handle)

class Master:

    def __init__(self):
        self.modbuses = []

    def get_modbus_master(self, xml_file, xsd_file):
        if os.path.isfile(xml_file):
            dom_modbus = etree.parse(xml_file)
            try:
                if dom_modbus.xpath('//modbuses'):
                    if ast.literal_eval(dom_modbus.xpath('//modbuses/@enabled')[0]):
                        modbuses = dom_modbus.xpath('//modbuses/*')
                        for m in modbuses:
                            host = m.attrib['host']
                            delay = m.xpath('./delay/text()')[0]
                            modbus = Modbus(host,delay)
                            slaves = m.xpath('./slaves/*')
                            for s in slaves:
                                slave_id = int(s.attrib['id'])
                                slave = modbus.add_slave(slave_id)
                                logger.debug('Added slave with id %s.', slave_id)
                                for b in s.xpath('./blocks/*'):
                                    name = b.attrib['name']
                                    request_type = b.xpath('./type/text()')[0]
                                    start_addr = int(b.xpath('./starting_address/text()')[0])
                                    size = int(b.xpath('./size/text()')[0])
                                    slave.add_block(name, request_type, start_addr,size)
                                    logger.debug(
                                        'Added block %s to slave %s. '
                                        '(type=%s, start=%s, size=%s)',
                                        name, slave_id, request_type, start_addr, size)
                            master.modbuses.append(modbus)
            except (Exception) as e:
                logger.info(e)
        else:
            logger('No template found. Service will remain unconfigured/stopped.')


class Modbus:

    def __init__(self, host, delay):
        self.host = host
        self.delay = delay
        self._slaves = {}

    def add_slave(self, slave_id, unsigned=True):
        """Add a new slave with the given id"""
        if (slave_id <= 0) or (slave_id > 255):
            logger.error('Invalid slave id %s',slave_id)
        if not self._slaves.has_key(slave_id):
            self._slaves[slave_id] = Slave(slave_id, unsigned)
            return self._slaves[slave_id]
        else:
            logger('Slave %s already exists',slave_id)

    def get_slave(self, slave_id):
        if self._slaves.has_key(slave_id):
            return self._slaves[slave_id]
        else:
            logger.error('Slave %s do not exist' ,slave_id)

class Slave:

    def __init__(self, id, unsigned=True):
        self._id = id
        self.unsigned = unsigned
        self._blocks = {} # the map registring all blocks of the slave


    def add_block(self, block_name, block_type, starting_address, size):
        if size <= 0:
            logger.error('size must be a positive number')
        if starting_address < 0:
            logger.error('starting address must be zero or positive number')
        if self._blocks.has_key(block_name):
            logger.error('Block %s already exists.',block_name)
        self._blocks[block_name] = Block(starting_address, size)




class Block:
    """This class represents the values for a range of addresses"""

    def __init__(self, starting_address, size):
        """
        Contructor: defines the address range and creates the array of values
        """
        self.starting_address = starting_address
        self._data = [0]*size
        self.size = len(self._data)

    def is_in(self, starting_address, size):
        """
        Returns true if a block with the given address and size
        would overlap this block
        """
        if starting_address > self.starting_address:
            return (self.starting_address+self.size)>starting_address
        elif starting_address < self.starting_address:
            return (starting_address+size)>self.starting_address
        return True


master = Master()
master.get_modbus_master('/Users/tangjiashan/workspace/conpot/conpot/emulators/mmaster/mmaster.xml','/Users/tangjiashan/workspace/conpot/conpot/emulators/mmaster/mmaster.xsd')
