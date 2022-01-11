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

#
#   Weather update server
#   Binds PUB socket to tcp://*:5556
#   Publishes random weather updates
#

import zmq
from random import randrange

# Get the context
context = zmq.Context()

# This is a proxy. We create the XSUB and XPUB endpoints
print ("This is proxy: creating xsub and xpubsockets")
xsubsocket = context.socket(zmq.XSUB)
xsubsocket.bind("tcp://*:5555")
xsubsocket.setsockopt(zmq.SUBSCRIBE, b'')  # everything

xpubsocket = context.socket (zmq.XPUB)
xpubsocket.setsockopt(zmq.XPUB_VERBOSE, 1)
xpubsocket.bind ("tcp://*:5556")

# This proxy is needed to connect the two sockets.
# But what this means is that we cannot do anything here.
# We are just relaying things internally.
# This blocks
zmq.proxy (xsubsocket, xpubsocket)

