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

# Task worker
# Connects PULL socket to tcp://localhost:5557
# Collects workloads from ventilator via that socket
# Connects PUSH socket to tcp://localhost:5558
# Sends results to sink via that socket
#
# Author: Lev Givon <lev(at)columbia(dot)edu>

import sys
import time
import zmq

context = zmq.Context()

# Note that we as a worker will PULL info from the source. So our role is that of
# a PULL.
# Socket to receive messages on
receiver = context.socket(zmq.PULL)
# Here we assume the source server runs locally unless we
# send a command line arg like 10.0.0.1
srv_addr = sys.argv[1] if len(sys.argv) > 2 else "localhost"
src_connect_str = "tcp://" + srv_addr + ":5557"
receiver.connect(src_connect_str)

# Remember that when we are done, we send our outcomes to
# the sink. So we do a PUSH as a client
# Socket to send messages to
sender = context.socket(zmq.PUSH)
# Here we assume the sink server runs locally unless we
# send a command line arg like 10.0.0.1
srv_addr = sys.argv[2] if len(sys.argv) > 2 else "localhost"
sink_connect_str = "tcp://" + srv_addr + ":5558"
sender.connect(sink_connect_str)

# Process tasks forever
while True:
    # Note, we pull from the source as a receiver
    s = receiver.recv()

    # Simple progress indicator for the viewer
    sys.stdout.write('.')
    sys.stdout.flush()

    # Do the work
    time.sleep(int(s)*0.001)

    # Note, we send to sink as a sender.
    # Send results to sink
    sender.send(b'')
