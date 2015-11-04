import binascii
import sys

data = '\x01\x03\x0A\x02\x01\x00\x02\x00\x03\x00\x04\x00\x05'

byte_data = bytearray(data)

while 1:
    q = sys.stdin.readline().rstrip()
    print str((1, 2, 'abc'))
    if str(q) == "b":
        bytearray
        print ' '.join(format(x, 'b') for x in bytearray(data))