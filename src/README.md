# RDMA Man-in-the-Middle Attack

We have a simple three host setup, client and server are both connected to a middle box, which implements a relay for RDMA packets.

The code base is organized as follows:
- [application](application) contains the unmodified client/server RDMA application.
- [relay](relay) contains the relay software and attacker code to watch and/or inject packets into the connection.

