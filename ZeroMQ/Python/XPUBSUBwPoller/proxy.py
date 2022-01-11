# Sample code for CS6381
# Vanderbilt University
# Instructor: Aniruddha Gokhale
#
# Code taken from ZeroMQ examples with additional
# comments or extra statements added to make the code
# more self-explanatory  or tweak it for our purposes
#
# We are executing these samples on a Mininet-emulated environment
#
#

# system and time
import os
import sys
import time

import zmq
from random import randrange

print ("ZMQ version = {}, PyZMQ version = {}".format (zmq.zmq_version (), zmq.pyzmq_version ()))
       
# Get the context
context = zmq.Context()

# This is a proxy. We create the XSUB and XPUB endpoints
print ("This is proxy: creating xsub and xpubsockets")
xsubsocket = context.socket(zmq.XSUB)
xsubsocket.bind("tcp://*:5555")

xpubsocket = context.socket (zmq.XPUB)
xpubsocket.setsockopt(zmq.XPUB_VERBOSE, 1)
xpubsocket.bind ("tcp://*:5556")

# Now we are going to create a poller
poller = zmq.Poller ()
poller.register (xsubsocket, zmq.POLLIN)
poller.register (xpubsocket, zmq.POLLIN)

while True:
    try:
        print ("Poll with a timeout of 1 sec")

        events = dict (poller.poll (1000))
        print ("Events received = {}".format (events))
        
        # Is there any data from publisher? Note that the proxy
        # will get only that data for which it has relayed
        # subscriptions to the publisher. Note that ZMQ in recent
        # versions is doing filtering on the publisher side. Thus,
        # not all data from publishers will even show up on proxy.
        if xsubsocket in events:
            msg = xsubsocket.recv_multipart()

            print ("Publication = {}".format (msg))

            # send the message to subscribers
            xpubsocket.send_multipart (msg)

        # Is there any data from subscriber? Note, this is
        # needed because we must relay the subscription info
        # to all my publishers else they will never send anything
        # to us given that we are a XSUB/XPUB entity
        if xpubsocket in events:
            msg = xpubsocket.recv_multipart()

            # parse the incoming message
            print ("subscription = {}".format (msg))

            # send the subscription info to publishers
            xsubsocket.send_multipart(msg)

    except:
        print "Exception thrown: ", sys.exc_info()[0]

