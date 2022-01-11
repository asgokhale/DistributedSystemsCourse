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
#   Hello World client in Python
#   Connects REQ socket to tcp://localhost:5555
#   Sends "Hello" to server, expects "World" back
#
# Added more comments

import sys

# we need to import this package
import zmq

print("Current libzmq version is %s" % zmq.zmq_version())
print("Current  pyzmq version is %s" % zmq.__version__)

# To use ZMQ, every session needs this singleton context object
context = zmq.Context()

#  Socket to talk to server. Note that because the client is the "requestor", we
# create a socket of type REQ
print ("Connecting to hello world server ...")
socket = context.socket(zmq.REQ)

# Here we assume a server runs locally unless we
# send a command line arg like 10.0.0.2
srv_addr = sys.argv[1] if len(sys.argv) > 1 else "localhost"
connect_str = "tcp://" + srv_addr + ":5555"
socket.connect (connect_str)

#  Do 10 requests, waiting each time for a response
for request in range (10):
    print("Sending request %s ..." % request)
    socket.send(b"Hello")

    #  Get the reply.
    message = socket.recv()
    print("Received reply %s [ %s ]" % (request, message))
