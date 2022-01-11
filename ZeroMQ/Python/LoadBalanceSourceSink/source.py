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


# Task ventilator
# Binds PUSH socket to tcp://localhost:5557
# Sends batch of tasks to workers via that socket
#
# Author: Lev Givon <lev(at)columbia(dot)edu>

import zmq
import random
import time
import sys

try:
    raw_input
except NameError:
    # Python 3
    raw_input = input

context = zmq.Context()

# Note, this code may start looking a bit complex. Remember we are the source.
# We need to send stuff to our workers for them to work on. When the workers are
# done, they will send their results to a sink. So we need to signal to our
# sink that we are starting.
#
# To that end, we first declare ourselves as the source by indicating our role with the
# PUSH action (to push things to the workers). In that role we are a server and hence
# we bind to a port
# 
# Socket to send messages on
sender = context.socket(zmq.PUSH)
sender.bind("tcp://*:5557")

# Next we also play the role of a one-time client by pushing a start signal to
# our sink (who is the sink server)
# Socket with direct access to the sink: used to syncronize start of batch
sink = context.socket(zmq.PUSH)

# Here we assume the sink server runs locally unless we
# send a command line arg like 10.0.0.2
srv_addr = sys.argv[1] if len(sys.argv) > 1 else "localhost"
sink_connect_str = "tcp://" + srv_addr + ":5558"
sink.connect(sink_connect_str)

# This is just a manually created barrier synchronization
print("Press Enter when the workers are ready: ")
_ = raw_input()
print("Sending tasks to workers...")

# The first message is "0" and signals start of batch
sink.send(b'0')

# Initialize random number generator
random.seed()

# Send 100 tasks
total_msec = 0
for task_nbr in range(100):

    # Random workload from 1 to 100 msecs
    workload = random.randint(1, 100)
    total_msec += workload

    sender.send_string(u'%i' % workload)

print("Total expected cost: %s msec" % total_msec)

# Give 0MQ time to deliver
time.sleep(1)
