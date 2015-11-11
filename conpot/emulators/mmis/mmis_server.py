import socket
import sys
import binascii
import time

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('0.0.0.0', 3000)
print >> sys.stderr, 'starting up on %s port %s' % server_address
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

while True:
    # Wait for a connection
    print >> sys.stderr, 'waiting for a connection'
    connection, client_address = sock.accept()

    try:
        print >> sys.stderr, 'connection from', client_address
        # Receive the data in small chunks and retransmit it
        while True:
            data = connection.recv(1)
            if data == '\x13':
                data = connection.recv(1)
                if data == '\x27':
                    print >> sys.stderr, 'sending data back to the client'
                    connection.sendall('\x19\x27\x01\x00\xff\xff\xff\xff\x00\x00\x00\x00\x08\x00\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x43')
                    connection.sendall('\x13\x27\x01\x00\x00\x00\x00\x00\x01\x00\x3c')
                    connection.sendall('\x19\x27\x01\x00\xff\xff\xff\xff\x00\x00\x00\x00\x08\x00\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x43')
                    connection.sendall('\x19\x27\x01\x00\xff\xff\xff\xff\x00\x00\x00\x00\x08\x00\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x43')
                    time.sleep(5)
                    connection.sendall('\x15\x27\x01\x00\x00\x00\x00\x00\x01\x00\x3e')
    finally:
        # Clean up the connection
        connection.close()