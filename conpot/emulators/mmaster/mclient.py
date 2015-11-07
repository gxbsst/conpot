from pymodbus.client.sync import ModbusTcpClient
import master
class MClient(master.Master):


    def connect(self):
        for m in self.master.modbuses:
            client = ModbusTcpClient('127.0.0.1')

