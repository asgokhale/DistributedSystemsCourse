#!/bin/sh
rm -fr *.out  # remove any existing out files
# now run each instance. The > redirects standard output to the
# named file after it, and then the 2> redirects the standard error
# to the arg named after it, which happens to the same file name
# as where we redirected the standard output. The final & is to
# push the command into the background and let it run.
#
# You can use such a logic and additional params to create
# all kinds of experimental scenarios.
python3 DiscoveryAppln.py -P 5 -S 4 > discovery.out 2>&1 &
python3 PublisherAppln.py -T 5 -n pub1 -p 5570 > pub1.out 2>&1 &
python3 PublisherAppln.py -T 5 -n pub2 -p 5571 > pub2.out 2>&1 &
python3 PublisherAppln.py -T 5 -n pub3 -p 5572 > pub3.out 2>&1 &
python3 PublisherAppln.py -T 5 -n pub4 -p 5573 > pub4.out 2>&1 &
python3 PublisherAppln.py -T 5 -n pub5 -p 5574 > pub5.out 2>&1 &
python3 SubscriberAppln.py -T 4 -n sub1 > sub1.out 2>&1 &
python3 SubscriberAppln.py -T 5 -n sub2 > sub2.out 2>&1 &
python3 SubscriberAppln.py -T 4 -n sub3 > sub3.out 2>&1 &
python3 SubscriberAppln.py -T 5 -n sub4 > sub4.out 2>&1 &
