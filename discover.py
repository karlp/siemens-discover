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
        # First two bytes are command codes?
        cmd,mac = struct.unpack_from(">H6s", data)
        self.mac = binascii.hexlify(mac)
        self.swv = "?"
        self.blv = "?"
        self.plantid = ""
        logging.debug("command = %d(%x), mac=%s", cmd, cmd, binascii.hexlify(mac))
        net_offs = 8
        if cmd == 0x3211:
            self.product = data[20:20+20].strip().strip("\0")
            self.plantid = data[20+20:20+20+32].strip().strip("\0")
        if cmd == 0x3612:
            net_offs = 8 + 12
            # Bigger packet replies, here...
            # cmd, mac, ?6 bytes?, mac again, net details, block of 44 0xff, then product for 52, then ?? to the end
            self.product = data[20+12+44:20+12+44+20].strip().strip("\0")
            self.plantid = data[20+12+44+20:20+12+44+20+32].strip().strip("\0")
            swv = struct.unpack_from("cBBB", data, 20+12+44+52+8)
            self.swv = "%c%d.%d.%d" % swv
            blv = struct.unpack_from("cBBB", data, 20+12+44+52+12)
            self.blv = "%c%d.%d.%d" % blv

        net = struct.unpack_from(">III", data, net_offs)
        self.ip = socket.inet_ntoa(struct.pack('>I',net[0]))
        self.netmask = socket.inet_ntoa(struct.pack('>I',net[1]))
        self.gw = socket.inet_ntoa(struct.pack('>I',net[2]))

    def __repr__(self):
        return "product=%(product)s (plant=%(plantid)s) {ip=%(ip)s, netmask=%(netmask)s, gw=%(gw)s} {SW ver: %(swv)s, Boot ver: %(blv)s}" % self.__dict__

def send_probe(src_addr, cmd=0x3101, target_mac="ffffffffffff"):
    # broadcast cmd, and broadcast mac (3101 works with specific macs too)
    data = struct.pack(">H6s", cmd, binascii.unhexlify(target_mac))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((src_addr, SIEMENS_DISC_PORT_MASTER))
    bs = sock.sendto(data, ("255.255.255.255", SIEMENS_DISC_PORT_DEVICE))
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
    # Send this once you have a mac, to get the fw version and bootloader version, if desired...
    #send_probe("192.168.255.124", cmd=0x3501, target_mac="20bbc602192a")

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