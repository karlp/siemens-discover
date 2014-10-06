#!/usr/bin/env python
# Karl Palsson, <karlp@tweak.net.au>, October 2014
# Rudimentary tool to scan for Siemens Sentron Power meters on your network
# Tested against a Sentron PAC4200, but _believed_ to work for anything in the system
# Determined via packet capture from the "Sentron powerconfig v3.2" tool
__author__ = 'karlp@tweak.net.au'


import binascii
import logging
import select
import socket
import struct
import time

# How long to wait for replies from devices (In whole seconds)
REPLY_TIMEOUT = 2

SIEMENS_DISC_PORT_MASTER = 17009
SIEMENS_DISC_PORT_DEVICE = 17008

logging.basicConfig(level=logging.WARN)

class SiemensDevice():
    def __init__(self, data):
        # First 8 bytes are unknown...
        logging.debug("Unknown bytes(8): %s", binascii.hexlify(data[:8]))
        net = struct.unpack_from(">III", data, 8)
        self.ip = socket.inet_ntoa(struct.pack('>I',net[0]))
        self.netmask = socket.inet_ntoa(struct.pack('>I',net[1]))
        self.gw = socket.inet_ntoa(struct.pack('>I',net[2]))
        self.product = data[20:].strip()

    def __repr__(self):
        return "product=%(product)s {ip=%(ip)s, netmask=%(netmask)s, gw=%(gw)s}" % self.__dict__

def send_probe(src_addr):
    data = "3101ffffffffffff"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((src_addr, SIEMENS_DISC_PORT_MASTER))
    bs = sock.sendto(binascii.unhexlify(data), ("255.255.255.255", SIEMENS_DISC_PORT_DEVICE))
    logging.info("Sent %d bytes from addres: %s", bs, src_addr)
    sock.close()

def listen(src):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", SIEMENS_DISC_PORT_MASTER))
    sock.setblocking(0)
    return sock

if __name__ == "__main__":
    # Need to iterate over all available interfaces....
    s = listen("blah")
    start = time.time()
    send_probe("192.168.255.124")

    while time.time() - start < REPLY_TIMEOUT:
        # Should really calculate timeout from current time, but worst case is only 2*REPLY_TIMEOUT
        # Should never get any errors on UDP listeners?
        rr, rw, err = select.select([s], [], [s], REPLY_TIMEOUT)
        for ss in rr:
            d = ss.recv(1024)
            if d:
                logging.debug("got %s", binascii.hexlify(d))
                print("Found a device: %s" % SiemensDevice(d))
            else:
                logging.warn("Failed to read from a ready socket, in UDP?! %s", ss)
        for ss in err:
            logging.warn("Got an error on a UDP Listen socket?!: %s", ss)
    s.close()