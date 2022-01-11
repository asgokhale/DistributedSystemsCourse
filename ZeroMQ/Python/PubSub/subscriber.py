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
#   Weather update client
#   Connects SUB socket to tcp://localhost:5556
#   Collects weather updates and finds avg temp in zipcode
#

import sys
import zmq

#  Socket to talk to server
context = zmq.Context()

# Since we are the subscriber, we use the SUB type of the socket
socket = context.socket(zmq.SUB)

# Here we assume publisher runs locally unless we
# send a command line arg like 10.0.0.1
srv_addr = sys.argv[1] if len(sys.argv) > 1 else "localhost"
connect_str = "tcp://" + srv_addr + ":5556"

print("Collecting updates from weather server...")
socket.connect(connect_str)

# Subscribe to zipcode, default is NYC, 10001
zip_filter = sys.argv[2] if len(sys.argv) > 2 else "10001"

# Python 2 - ascii bytes to unicode str
if isinstance(zip_filter, bytes):
    zip_filter = zip_filter.decode('ascii')

# any subscriber must use the SUBSCRIBE to set a subscription, i.e., tell the
# system what it is interested in
socket.setsockopt_string(zmq.SUBSCRIBE, zip_filter)

# Process 10 updates
total_temp = 0
for update_nbr in range(10):
    string = socket.recv_string()
    zipcode, temperature, relhumidity = string.split()
    total_temp += int(temperature)

print("Average temperature for zipcode '%s' was %dF" % (
      zip_filter, total_temp / (update_nbr+1))
)
