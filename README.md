# Payment Gateways Virtual Network Function

## Overview
Payment Gateways VNF is based on netfilter iptables and delivers easy and convinient way to manage payment gateways ipv4 addresses. The main idea behind this approach is to handle packets only on IP layer. Packets destined to payment gateway are accepted and forwarded, other HTTP (port 80) traffic is transparently redirected to the portal login page. Furthermore this approach is not limited only to payment gateways but can accept any opengarden domains.

## Installation
To easily install pgw one can use Ansible playbook pgw.yml.
As a base image it is recommened to use Ubuntu 14.04.
VNF has 3 interfaces, eth1 and eth2 are defined in playbook:
```
    eth_in_dev: eth1
    eth_out_dev: eth2
    eth_out_ip: 192.168.1.18
    eth_out_nm: 255.255.255.0
    eth_out_gw: 192.168.1.1
```
eth0 is management interface and must be defined manually before installation process:
```
auto eth0
iface eth0 inet static
	address 10.0.0.101
	netmask 255.255.255.0
```
pay attention on gateway definition, if you will define gateway for eth0 it will be used as a default route.

To run playbook (on the remote Ansible control host) issue:
```
sudo ansible-galaxy install bennojoy.network_interface
ansible-playbook -s -u ubuntu -K pgw.yml -i invetory
```
where invetory file may look like:
```
[vnfs]
10.0.0.101
```
where 10.0.0.101 is a management ip address mentioned earlier.

## REST API
VNF is equipped with RESTful API to peer with orchestrating system. Here are the available REST API operations:
