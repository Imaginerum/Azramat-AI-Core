# 2025-10-16 16:54:07 by RouterOS 7.19.6
# software id = 5E4M-YJ2X
#
# model = L009UiGS-2HaxD
# serial number = HJD0A3BERQD
/interface bridge
add admin-mac=F4:1E:57:F6:38:6A auto-mac=no comment=defconf name=bridge
/interface list
add comment=defconf name=WAN
add comment=defconf name=LAN
/interface wifi security
add authentication-types=wpa3-psk disabled=no name=sec1
/interface wifi
set [ find default-name=wifi1 ] channel.band=2ghz-n .skip-dfs-channels=\
    10min-cac .width=20mhz configuration.mode=ap .ssid=Ulala disabled=no mtu=\
    1500 security=sec1 security.authentication-types=wpa2-psk,wpa3-psk .ft=\
    yes .ft-over-ds=yes
/ip firewall layer7-protocol
add name=dom
/ip ipsec policy group
add name=ikev2-group
add name=ikev2-policy
add name=ikev2-templates
add name=ikev2-policys
/ip ipsec profile
set [ find default=yes ] dh-group=modp2048 dpd-interval=2m \
    dpd-maximum-failures=5 enc-algorithm=aes-256 hash-algorithm=sha256 \
    lifetime=3d
add dh-group=modp2048 dpd-interval=2m enc-algorithm=aes-256 hash-algorithm=\
    sha256 lifetime=1w name=ikev2-profile
/ip ipsec peer
add exchange-mode=ike2 name=ikev2-peer passive=yes profile=ikev2-profile
/ip ipsec proposal
set [ find default=yes ] auth-algorithms=sha256 enc-algorithms=aes-256-cbc \
    lifetime=3h pfs-group=none
add auth-algorithms=sha256 enc-algorithms=aes-256-cbc lifetime=1d name=\
    ikev2-esp pfs-group=modp2048
/ip pool
add name=default-dhcp ranges=192.168.88.10-192.168.88.170
add name=ikev2-pool ranges=192.168.89.10-192.168.89.50
/ip dhcp-server
add address-pool=default-dhcp interface=bridge name=defconf
/ip ipsec mode-config
add address-pool=ikev2-pool name=ikev2-cfg split-include=192.168.88.0/24 \
    static-dns=192.168.88.1,1.1.1.1 system-dns=no
/port
set 0 name=serial0
/ppp profile
add bridge=bridge local-address=192.168.88.1 name=ikev2-profile \
    remote-address=ikev2-pool use-encryption=yes
/disk settings
set auto-media-interface=bridge auto-media-sharing=yes auto-smb-sharing=yes
/interface bridge port
add bridge=bridge comment=defconf interface=ether2
add bridge=bridge comment=defconf interface=ether3
add bridge=bridge comment=defconf interface=ether4
add bridge=bridge comment=defconf interface=ether5
add bridge=bridge comment=defconf interface=ether6
add bridge=bridge comment=defconf interface=ether7
add bridge=bridge comment=defconf interface=ether8
add bridge=bridge comment=defconf interface=sfp1
add bridge=bridge comment=defconf interface=wifi1
/ip neighbor discovery-settings
set discover-interface-list=LAN
/interface detect-internet
set detect-interface-list=all
/interface list member
add comment=defconf interface=bridge list=LAN
add comment=defconf interface=ether1 list=WAN
/ip address
add address=192.168.88.1/24 comment=defconf interface=bridge network=\
    192.168.88.0
/ip cloud
set ddns-enabled=yes
/ip dhcp-client
add comment=defconf interface=ether1
/ip dhcp-server lease
add address=192.168.88.250 client-id=1:3c:ec:ef:76:6f:54 mac-address=\
    3C:EC:EF:76:6F:54 server=defconf
add address=192.168.88.252 client-id=\
    ff:be:ef:10:1:0:1:0:1:30:52:b3:c3:bc:24:11:97:e7:b0 mac-address=\
    DE:AD:BE:EF:10:01 server=defconf
add address=192.168.88.100 client-id=\
    ff:ca:53:9:5a:0:2:0:0:ab:11:cc:e1:fe:60:0:2e:32:dc mac-address=\
    BC:24:11:EC:FB:D4 server=defconf
add address=192.168.88.251 client-id=\
    ff:be:ef:10:3:0:1:0:1:30:52:b3:c3:bc:24:11:97:e7:b0 mac-address=\
    DE:AD:BE:EF:10:03 server=defconf
add address=192.168.88.253 client-id=\
    ff:be:ef:10:2:0:1:0:1:30:52:b3:c3:bc:24:11:97:e7:b0 mac-address=\
    DE:AD:BE:EF:10:02 server=defconf
/ip dhcp-server network
add address=192.168.88.0/24 comment=defconf dns-server=192.168.88.1 gateway=\
    192.168.88.1
/ip dns
set allow-remote-requests=yes
/ip dns static
add address=192.168.88.1 comment=defconf name=router.lan type=A
add address=192.168.88.10 name=vps1.swilak.pl type=A
add address=192.168.88.254 name=vps.swilak.pl type=A
add address=192.168.88.252 match-subdomain=yes name=swilak.pl type=A
add address=192.168.88.252 name=mail.swilak.pl type=A
add address=192.168.88.252 match-subdomain=yes name=azramat.pl type=A
add address=192.168.88.252 name=mail.azramat.pl type=A
add address=192.168.88.252 address-list=. name=lamp.swilak.pl type=A
add address=192.168.88.252 name=phpmyadmin.swilak.pl type=A
add address=192.168.88.252 name=pgadmin.swilak.pl type=A
/ip firewall filter
add action=accept chain=forward comment=\
    "IPsec in -> allow (before fasttrack)" ipsec-policy=in,ipsec
add action=accept chain=input comment="ALLOW IPsec ESP" protocol=ipsec-esp
add action=accept chain=forward comment="IKEv2 clients -> LAN" src-address=\
    192.168.89.0/24
add action=accept chain=forward comment="IKEv2 VPN to LAN" dst-address=\
    192.168.88.0/24 src-address=192.168.89.0/24
add action=accept chain=input comment="ALLOW established,related,untracked" \
    connection-state=established,related,untracked
add action=accept chain=input comment="ALLOW ping" protocol=icmp
add action=accept chain=input comment="ALLOW loopback" dst-address=127.0.0.1
add action=accept chain=input comment="ALLOW WinBox from WAN" dst-port=\
    8291,22 in-interface=ether1 protocol=tcp
add action=accept chain=input comment="ALLOW IKEv2" dst-port=500,4500 \
    protocol=udp
add action=accept chain=input comment="IKEv2 clients -> router" src-address=\
    192.168.89.0/24
add action=accept chain=input comment="allow web to router" dst-port=80,443 \
    protocol=tcp
add action=accept chain=forward comment="ALLOW DNAT services" \
    connection-nat-state=dstnat
add action=drop chain=input comment="DROP invalid" connection-state=invalid
add action=drop chain=input comment=\
    "DROP all not from LAN (except allowed above)" in-interface-list=!LAN
/ip firewall nat
add action=accept chain=srcnat comment="No NAT for IPsec" ipsec-policy=\
    out,ipsec
add action=masquerade chain=srcnat comment="defconf: masquerade" \
    ipsec-policy=out,none out-interface-list=WAN
add action=masquerade chain=srcnat comment="Masquerade LAN->WAN" \
    ipsec-policy=out,none out-interface-list=WAN
add action=masquerade chain=srcnat comment=\
    "NAT for IKEv2 clients (internet przez MT)" src-address=192.168.89.0/24
add action=dst-nat chain=dstnat comment="WWW 80" dst-port=80 in-interface=\
    ether1 protocol=tcp to-addresses=192.168.88.252 to-ports=80
add action=dst-nat chain=dstnat comment="WWW 443" dst-port=443 in-interface=\
    ether1 protocol=tcp to-addresses=192.168.88.252 to-ports=443
add action=dst-nat chain=dstnat comment="MAIL SMTP" dst-port=25 in-interface=\
    ether1 protocol=tcp to-addresses=192.168.88.252 to-ports=25
add action=dst-nat chain=dstnat comment="MAIL IMAP" dst-port=143 \
    in-interface=ether1 protocol=tcp to-addresses=192.168.88.252 to-ports=143
add action=dst-nat chain=dstnat comment="MAIL SUBMISSION" dst-port=587 \
    in-interface=ether1 protocol=tcp to-addresses=192.168.88.252 to-ports=587
add action=dst-nat chain=dstnat comment="MAIL IMAPS" dst-port=993 \
    in-interface=ether1 protocol=tcp to-addresses=192.168.88.252 to-ports=993
/ip firewall service-port
set ftp disabled=yes
set tftp disabled=yes
set sip disabled=yes
set pptp disabled=yes
/ip ipsec identity
add auth-method=digital-signature certificate=server-cert generate-policy=\
    port-override mode-config=ikev2-cfg peer=ikev2-peer \
    policy-template-group=ikev2-policy
/ip ipsec policy
add comment="IKEv2 split 88/24" dst-address=192.168.88.0/24 group=\
    ikev2-policy proposal=ikev2-esp src-address=0.0.0.0/0 template=yes
add comment="IKEv2 permissive 0/0" dst-address=0.0.0.0/0 group=ikev2-policy \
    proposal=ikev2-esp src-address=0.0.0.0/0 template=yes
add comment="IKEv2 split 88/24" dst-address=192.168.88.0/24 group=\
    ikev2-policy src-address=0.0.0.0/0 template=yes
add comment="IKEv2 permissive 0/0" dst-address=0.0.0.0/0 group=ikev2-policy \
    src-address=0.0.0.0/0 template=yes
/ip service
set ftp disabled=yes
set telnet disabled=yes
set www disabled=yes
set api disabled=yes
set api-ssl disabled=yes
/ipv6 firewall address-list
add address=::/128 comment="defconf: unspecified address" list=bad_ipv6
add address=::1/128 comment="defconf: lo" list=bad_ipv6
add address=fec0::/10 comment="defconf: site-local" list=bad_ipv6
add address=::ffff:0.0.0.0/96 comment="defconf: ipv4-mapped" list=bad_ipv6
add address=::/96 comment="defconf: ipv4 compat" list=bad_ipv6
add address=100::/64 comment="defconf: discard only " list=bad_ipv6
add address=2001:db8::/32 comment="defconf: documentation" list=bad_ipv6
add address=2001:10::/28 comment="defconf: ORCHID" list=bad_ipv6
add address=3ffe::/16 comment="defconf: 6bone" list=bad_ipv6
/ipv6 firewall filter
add action=accept chain=input comment=\
    "defconf: accept established,related,untracked" connection-state=\
    established,related,untracked
add action=drop chain=input comment="defconf: drop invalid" connection-state=\
    invalid
add action=accept chain=input comment="defconf: accept ICMPv6" protocol=\
    icmpv6
add action=accept chain=input comment="defconf: accept UDP traceroute" \
    dst-port=33434-33534 protocol=udp
add action=accept chain=input comment=\
    "defconf: accept DHCPv6-Client prefix delegation." dst-port=546 protocol=\
    udp src-address=fe80::/10
add action=accept chain=input comment="defconf: accept IKE" dst-port=500,4500 \
    protocol=udp
add action=accept chain=input comment="defconf: accept ipsec AH" protocol=\
    ipsec-ah
add action=accept chain=input comment="defconf: accept ipsec ESP" protocol=\
    ipsec-esp
add action=accept chain=input comment=\
    "defconf: accept all that matches ipsec policy" ipsec-policy=in,ipsec
add action=drop chain=input comment=\
    "defconf: drop everything else not coming from LAN" in-interface-list=\
    !LAN
add action=fasttrack-connection chain=forward comment="defconf: fasttrack6" \
    connection-state=established,related
add action=accept chain=forward comment=\
    "defconf: accept established,related,untracked" connection-state=\
    established,related,untracked
add action=drop chain=forward comment="defconf: drop invalid" \
    connection-state=invalid
add action=drop chain=forward comment=\
    "defconf: drop packets with bad src ipv6" src-address-list=bad_ipv6
add action=drop chain=forward comment=\
    "defconf: drop packets with bad dst ipv6" dst-address-list=bad_ipv6
add action=drop chain=forward comment="defconf: rfc4890 drop hop-limit=1" \
    hop-limit=equal:1 protocol=icmpv6
add action=accept chain=forward comment="defconf: accept ICMPv6" protocol=\
    icmpv6
add action=accept chain=forward comment="defconf: accept HIP" protocol=139
add action=accept chain=forward comment="defconf: accept IKE" dst-port=\
    500,4500 protocol=udp
add action=accept chain=forward comment="defconf: accept ipsec AH" protocol=\
    ipsec-ah
add action=accept chain=forward comment="defconf: accept ipsec ESP" protocol=\
    ipsec-esp
add action=accept chain=forward comment=\
    "defconf: accept all that matches ipsec policy" ipsec-policy=in,ipsec
add action=drop chain=forward comment=\
    "defconf: drop everything else not coming from LAN" in-interface-list=\
    !LAN
/ppp secret
add name=ekoit profile=ikev2-profile routes=192.168.88.0/24
add name=ekoit profile=ikev2-profile service=l2tp
/system clock
set time-zone-name=Europe/Warsaw
/system logging
add topics=ipsec,!packet
/system routerboard settings
set auto-upgrade=yes enter-setup-on=delete-key
/tool mac-server
set allowed-interface-list=LAN
/tool mac-server mac-winbox
set allowed-interface-list=LAN
