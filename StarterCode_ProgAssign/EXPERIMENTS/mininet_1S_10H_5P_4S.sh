h1 python3 DiscoveryAppln.py -P 5 -S 4 > discovery.out 2>&1 &
h2 python3 PublisherAppln.py -d "10.0.0.1:5555" -a "10.0.0.2" -T 5 -n pub1 > pub1.out 2>&1 &
h3 python3 PublisherAppln.py -d "10.0.0.1:5555" -a "10.0.0.3" -T 5 -n pub2 > pub2.out 2>&1 &
h4 python3 PublisherAppln.py -d "10.0.0.1:5555" -a "10.0.0.4" -T 5 -n pub3 > pub3.out 2>&1 &
h5 python3 PublisherAppln.py -d "10.0.0.1:5555" -a "10.0.0.5" -T 5 -n pub4 > pub4.out 2>&1 &
h6 python3 PublisherAppln.py -d "10.0.0.1:5555" -a "10.0.0.6" -T 5 -n pub5 > pub5.out 2>&1 &
h7 python3 SubscriberAppln.py -d "10.0.0.1:5555" -T 4 -n sub1 > sub1.out 2>&1 &
h8 python3 SubscriberAppln.py -d "10.0.0.1:5555" -T 5 -n sub2 > sub2.out 2>&1 &
h9 python3 SubscriberAppln.py -d "10.0.0.1:5555" -T 4 -n sub3 > sub3.out 2>&1 &
h10 python3 SubscriberAppln.py -d "10.0.0.1:5555" -T 5 -n sub4 > sub4.out 2>&1 &
