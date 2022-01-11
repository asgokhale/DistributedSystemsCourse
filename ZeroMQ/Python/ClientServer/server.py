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
#   Hello World server in Python
#   Binds REP socket to tcp://*:5555
#   Expects b"Hello" from client, replies with b"World"
#
#
# Based on the Hello World server example in ZeroMQ with
# more comments
#

import time
import zmq    # this package must be imported for ZMQ to work

print("Current libzmq version is %s" % zmq.zmq_version())
print("Current  pyzmq version is %s" % zmq.__version__)

# every ZMQ session requires a context
context = zmq.Context ()   # returns a singleton object

# The socket concept in ZMQ is far more advanced than the traditional socket in
# networking. Each socket we obtain from the context object must be of a certain
# type. In our case, we are supporting the role of a server, which technically
# means that we are going to reply to incoming client requests. Thus, the REP
# type is to be used for the socket type
socket = context.socket (zmq.REP)

# as in a traditional socket, tell the system what port are we going to listen on
# Moreover, tell it which protocol we are going to use, and which network
# interface we are going to listen for incoming requests. In our case, we will
# use TCP protocol, the * implies any available interface, and 5555 is the
# port num
socket.bind ("tcp://*:5555")

# since we are a server, we service incoming clients forever
while True:
    #  Wait for next request from client
    message = socket.recv()
    print("Received request: %s" % message)

    #  Do some 'work'. In this case we just sleep.
    time.sleep(1)

    #  Send reply back to client
    socket.send(b"World")
