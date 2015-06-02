# Payment Gateways Virtual Network Function

## Overview
Payment Gateways VNF is based on netfilter iptables and delivers easy and convinient way to manage payment gateways ipv4 addresses. The main idea behind this approach is to handle packets only on IP layer. Packets destined to payment gateway are accepted and forwarded, other HTTP (port 80) traffic is transparently redirected to the portal login page. Furthermore this approach is not limited only to payment gateways but can accept any opengarden domains.

## Installation
To easily install pgw one can use Ansible playbook pgw.yml.
As a base image it is recommened to use Ubuntu 14.04.
VNF has 3 interfaces, eth1 (in) and eth2 (out) are defined in playbook:
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

**pgws**

`GET`, `POST` `/pgw/api/v1.0/pgws` - returns list of payment gateway domains; adds single domain

**pgws/<int:id>**

`GET`, `DELETE` `/pgw/api/v1.0/pgws/<int:id>` - returns payment gateway domain; deletes single domain

**pgws/reload**

`GET` `/pgw/api/v1.0/pgws/reload` - reloads iptables with domain names

### REST API examples
```
curl -i http://10.0.0.101/pgw/api/v1.0/pgws
```
```
{
    "pgws": [
        {
            "domain": "www.paypal.com", 
            "uri": "http://10.0.0.101/pgw/api/v1.0/pgws/30"
        }, 
        {
            "domain": "paypal.com", 
            "uri": "http://10.0.0.101/pgw/api/v1.0/pgws/29"
        }, 
        {
            "domain": "login.wmtransfer.com", 
            "uri": "http://10.0.0.101/pgw/api/v1.0/pgws/28"
        }, 
        {
            "domain": "www.cyberplat.ru", 
            "uri": "http://10.0.0.101/pgw/api/v1.0/pgws/24"
        }, 
        {
            "domain": "www.webmoney.ru", 
            "uri": "http://10.0.0.101/pgw/api/v1.0/pgws/23"
        }, 
        {
            "domain": "unistream.ru", 
            "uri": "http://10.0.0.101/pgw/api/v1.0/pgws/7"
        }, 
        {
            "domain": "www.rbkmoney.ru", 
            "uri": "http://10.0.0.101/pgw/api/v1.0/pgws/6"
        }, 
        {
            "domain": "www.assist.ru", 
            "uri": "http://10.0.0.101/pgw/api/v1.0/pgws/5"
        }
    ]
}
```
``` 
curl -i -H "Content-Type: application/json" -X POST -d '{"domain":"www.webmoney.ru"}' http://10.0.0.101/pgw/api/v1.0/pgws
```
```
{
    "pgws": [
        {
            "domain": "www.webmoney.ru", 
            "uri": "http://10.0.0.101/pgw/api/v1.0/pgws/23"
        }, 
        {
            "domain": "unistream.ru", 
            "uri": "http://10.0.0.101/pgw/api/v1.0/pgws/7"
        }, 
        {
            "domain": "www.rbkmoney.ru", 
            "uri": "http://10.0.0.101/pgw/api/v1.0/pgws/6"
        }, 
        {
            "domain": "www.assist.ru", 
            "uri": "http://10.0.0.101/pgw/api/v1.0/pgws/5"
        }
    ]
}
```
result in iptables
```
sudo iptables -L -n -v -t nat
```
```
Chain PAYMENT_GW (1 references)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            37.139.14.218        /* www.assist.ru */
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            173.203.211.32       /* www.rbkmoney.ru */
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            62.76.46.181         /* unistream.ru */
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            217.23.144.177       /* www.webmoney.ru */
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            62.210.115.140       /* www.webmoney.ru */
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            37.187.104.200       /* www.webmoney.ru */
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            37.187.104.199       /* www.webmoney.ru */
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            89.108.126.29        /* www.webmoney.ru */
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            88.198.43.118        /* www.webmoney.ru */
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            109.72.129.48        /* www.cyberplat.ru */
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            91.200.28.56         /* login.wmtransfer.com */
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            91.227.52.56         /* login.wmtransfer.com */
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            66.211.169.66        /* paypal.com */
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            66.211.169.3         /* paypal.com */
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            23.59.86.34          /* www.paypal.com */

```
## Packet Flow
Before any packet processing will occur PGW VNF must be programmed with Orchestrator via REST API, then it translates payment gateways domain names to ip addresses and install them into iptables.

```

                                                    +------------------+                         
                                                    |                  |                         
                                                    |   ORCHESTRATOR   |                         
                                                    |                  |                         
                                                    +---------+--------+                         
                                                              | REST                             
                                                              |                                  
                                                              |                                  
                                                              | eth0                             
                           +----------+              +--------v-------+                          
                           |          |              |                |                          
+----------+               | BRAS/BNG |              |     PGW VNF    |           +-------------+
|SUBSCRIBER|  1            |          | 2            |                | 3         |             |
|          +--------------->          +-------------->        +-------------------> PAYMENT GW  |
|          |               |          |          eth1|        |       | eth2      |             |
+----------+               |          |              |        |PORTAL |           +-------------+
                           |          |              |        |       |                          
                           +----------+              +--------+-------+                          
```
1. Subscriber initiates http request to web-server in the Internet (DNS request will be transparently forwarded).
2. BNG somehow next-hops or next-interfaces packet to PGW VNF.
3. VNF processes all packets arrived on inbound interface eth1 with following rules:
```
Chain PREROUTING (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 ACCEPT     udp  --  eth1   *       0.0.0.0/0            0.0.0.0/0            udp dpt:53
    0     0 PAYMENT_GW  tcp  --  eth1   *       0.0.0.0/0            0.0.0.0/0           
    0     0 DNAT       tcp  --  eth1   *       0.0.0.0/0            0.0.0.0/0            tcp dpt:80 to:192.168.1.18:80
    0     0 DROP       all  --  eth1   *       0.0.0.0/0            0.0.0.0/0           
```
packets to payment gw are proccessed with nested chain PAYMENT_GW, which is build from domain names; if packet is not destined to payment gw and has destination port 80, it is transparently redirected to portal and landed to e.g. login page or payment gw link list page, all other traffic is dropped.
