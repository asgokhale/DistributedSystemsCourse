r1 route add -net 137.109.0.0 netmask 255.255.0.0 gw 174.173.1.2 dev r1-eth4
r1 route
r2 route add -net 145.198.0.0 netmask 255.255.0.0 gw 174.173.1.1 dev r2-eth4
r2 route
