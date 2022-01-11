# Sample code for CS6381
# Vanderbilt University
# Instructor: Aniruddha Gokhale
#
#
# Modified to use epgm multicast
#
#

#
#   Weather update server
#   Binds PUB socket to epgm://224.0.0.1:5555
#   Publishes random weather updates
#

import zmq
from random import randrange

print("Current libzmq version is %s" % zmq.zmq_version())
print("Current  pyzmq version is %s" % zmq.__version__)

context = zmq.Context()

# The difference here is that this is a publisher and its aim in life is
# to just publish some value. The binding is as before.
socket = context.socket(zmq.PUB)
#socket.bind("epgm://;224.0.0.3:5555")
socket.bind("epgm://;239.0.0.1:5555")

# keep publishing 
while True:
    zipcode = randrange(1, 100000)
    temperature = randrange(-80, 135)
    relhumidity = randrange(10, 60)

    socket.send_string("%i %i %i" % (zipcode, temperature, relhumidity))
