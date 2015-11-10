import socket
import binascii


TCP_IP = '0.0.0.0'
TCP_PORT = 9002
BUFFER_SIZE = 20  # Normally 1024, but we want fast response


class DCTServer(object):
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((TCP_IP, TCP_PORT))
        self.server.listen(1)
        self.conn = None
        self.closed = False

    def start(self):
        print 'Server start.'
        self.conn, address = self.server.accept()
        print 'Connection address:', address
        while not self.closed:
            data = self.conn.recv(BUFFER_SIZE)
            if not data:
                break
            print "received data:", binascii.hexlify(data)
            data_bytes = bytearray(data)
            if data_bytes[1] == 0x03:
                print "send 01030A00010002000300040005"
                self.conn.send('\x01\x03\x0A\x00\x01\x00\x02\x00\x03\x00\x04\x00\x05')
            elif data_bytes[1] == 0x10:
                self.conn.send('\x01\x10\x00\x14\x00\x01')

    def stop(self):
        self.closed = True
        self.conn.close()

DCTServer().start()