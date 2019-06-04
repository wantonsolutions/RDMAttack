#!/bin/bash

SCRIPT_PATH="$(realpath $0)"

client_host="b09-17"
server_host="b09-15"
middle_host="b09-05"

# RoCE interface config

client_ip="10.0.0.17"
server_ip="10.0.0.15"

# On real client/server machines
client_real_mac="ec:0d:9a:68:21:bc"
server_real_mac="ec:0d:9a:68:21:d0"
client_real_iface="eth0"
server_real_iface="eth0"

# On middle machine that fakes IPs and does forwarding
client_facing_mac="00:02:c9:45:25:b0"
server_facing_mac="00:02:c9:45:25:b1"
client_facing_iface="enp1s0"
server_facing_iface="enp1s0d1"

MTU=9000

setup_ip_client() {
    echo >&2 "Setting up IPs on client..."
    set -x
    sudo ifconfig $client_real_iface $client_ip netmask 255.255.255.0
    #sudo arp -d $server_ip
    sudo arp -s $server_ip $client_facing_mac
}

setup_ip_server() {
    echo >&2 "Setting up IPs on server..."
    set -x
    sudo ifconfig $server_real_iface $server_ip netmask 255.255.255.0
    #sudo arp -d $client_ip
    sudo arp -s $client_ip $server_facing_mac
}

setup_ip_middle() {
    echo >&2 "Setting up IPs on middle box..."
    set -x
    sudo ifconfig $client_facing_iface $server_ip netmask 255.255.255.0
    sudo ifconfig $server_facing_iface $client_ip netmask 255.255.255.0
    #sudo arp -d $client_ip
    #sudo arp -d $server_ip
    sudo arp -i $server_facing_iface -s $client_ip $client_real_mac
    sudo arp -i $client_facing_iface -s $server_ip $server_real_mac
}

setup_ip_all() {
    ssh $client_host "source $SCRIPT_PATH; setup_ip_client"
    ssh $server_host "source $SCRIPT_PATH; setup_ip_server"
    ssh $middle_host "source $SCRIPT_PATH; setup_ip_middle"
}

set_mtu() {
    host="$1"
    iface="$2"
    ssh $host "sudo ifconfig $iface mtu $MTU"
}

set_mtu_all() {
    set_mtu $client_host $client_real_iface
    set_mtu $server_host $server_real_iface
    set_mtu $middle_host $client_facing_iface
    set_mtu $middle_host $server_facing_iface
}

enable_promisc_mode() {
    host="$1"
    iface="$2"
    ssh $host "sudo ifconfig $iface promisc"
}

disable_promisc_mode() {
    host="$1"
    iface="$2"
    ssh $host "sudo ifconfig $iface -promisc"
}

setup_promisc_modes() {
    echo >&2 "Setting up promisc modes..."
    disable_promisc_mode $client_host $client_real_iface
    disable_promisc_mode $server_host $server_real_iface
    enable_promisc_mode $middle_host $client_facing_iface
    enable_promisc_mode $middle_host $server_facing_iface
}

enable_sniffer() {
    host="$1"
    iface="$2"
    ssh $host "sudo ethtool --set-priv-flags $iface sniffer on"
}

disable_sniffer() {
    host="$1"
    iface="$2"
    ssh $host "sudo ethtool --set-priv-flags $iface sniffer off"
}

enable_sniffer_all() {
    echo >&2 "Enabling all sniffers..."
    enable_sniffer $client_host $client_real_iface
    enable_sniffer $server_host $server_real_iface
    #enable_sniffer $middle_host $client_facing_iface
    #enable_sniffer $middle_host $server_facing_iface
}

disable_sniffer_all() {
    echo >&2 "Disabling all sniffers..."
    disable_sniffer $client_host $client_real_iface
    disable_sniffer $server_host $server_real_iface
    #disable_sniffer $middle_host $client_facing_iface
    #disable_sniffer $middle_host $server_facing_iface
}

setup_network() {
    setup_ip_all
    set_mtu_all
    setup_promisc_modes
    disable_sniffer_all
}

install_dependencies() {
    cmd="sudo apt-get update && sudo apt-get install -y pssh"
    ssh $client_host "$cmd"
    ssh $server_host "$cmd"
    ssh $middle_host "$cmd"
}

main() {
    set -e
    set -x
    #install_dependencies
    setup_network
}

if [ "$(basename $0)" = "$(basename $BASH_SOURCE)" ]; then
    main
fi

