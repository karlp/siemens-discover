#!/usr/bin/env python
# Karl Palsson, <karlp@tweak.net.au>, October 2014
# Rudimentary tool to scan for Siemens Sentron Power meters on your network
# Tested against a Sentron PAC4200, but _believed_ to work for anything in the system
# Determined via packet capture from the "Sentron powerconfig v3.2" tool
__author__ = 'karlp@tweak.net.au'


import binascii
import logging
import socket
import struct

SIEMENS_DISC_SEND_SRC = 17009
SIEMENS_DISC_SEND_DST = 17008

logging.basicConfig(level=logging.DEBUG)

def send_probe(src_addr):
    data = "3101ffffffffffff"

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
    sock.bind((src_addr, SIEMENS_DISC_SEND_SRC))
    bs = sock.sendto(binascii.unhexlify(data), ("255.255.255.255", SIEMENS_DISC_SEND_DST))
    logging.info("Sent %d bytes from addres: %s", bs, src_addr)
    sock.close()

if __name__ == "__main__":
    # Need to iterate over all available interfaces....
    send_probe("192.168.255.124")