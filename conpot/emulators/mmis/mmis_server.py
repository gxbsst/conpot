import socket
import sys
import binascii

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('localhost', 7000)
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
            data = connection.recv(31)
            print >> sys.stderr, 'received "%s"' % binascii.hexlify(data)
            if data:
                print >> sys.stderr, 'sending data back to the client'
                connection.sendall('\x19\x27\x01\x00\xff\xff\xff\xff\x00\x00\x00\x00\x08\x00\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x43')
                connection.sendall('\x13\x27\x01\x00\x00\x00\x00\x00\x01\x00\x3c')
                connection.sendall('\x19\x27\x01\x00\xff\xff\xff\xff\x00\x00\x00\x00\x08\x00\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x43')
                connection.sendall('\x19\x27\x01\x00\xff\xff\xff\xff\x00\x00\x00\x00\x08\x00\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x43')
            else:
                print >> sys.stderr, 'no more data from', client_address
                break
    finally:
        # Clean up the connection
        connection.close()