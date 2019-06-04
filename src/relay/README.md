# RoCE v2 packet relay

## Setup

We use `b09-17` as the client, `b09-15` as the server, and `b09-05` as the middle box, or the relay host. Client is connected to one of the ports on the middle box, and server connects to the other one.

We configure `arp` entries on client and servers such that client and server both think they are talking directly to each other, but in reality, we just forward the packets at the relay, which also gives us the ability to hijack packets.

## Packet Forwarding

We use `scapy`, a python framework for low-level (i.e. raw) packet construction, manipulation and sniffing/injection. With `scapy`, we are able to sniff packets off interfaces with filters, which in our case is `udp dst port 4791` aka RoCEv2 packets, re-write the Ethernet MAC source and destination addresses, and relay the packet out of the other interface.

We can optionally insert the attacker in this process, allowing the attacker to inspect, change and inject packets into the connection.

## Usage

- `setup.sh` is a shell script to set up the network configurations, including IPs, MTUs, promisc modes, etc.
    - Run this once before experiments to ensure correct configuration.
- `forward_rocev2_packets.py` starts forwarding of RoCE v2 packets on the provided interface.
    - Run it like `sudo python forward_rocev2_packets.py <iface>` for both interfaces.
    - Toggle the `VERBOSE` flag in the script as needed.
- Once both relays are running, you can run any RoCE applications between the client and server as normal.
    - For example, you can use `rdma_client/rdma_server` or `udaddy` to test connectivity.
    - Or you can run the client application provided in the [application](../application) directory.

