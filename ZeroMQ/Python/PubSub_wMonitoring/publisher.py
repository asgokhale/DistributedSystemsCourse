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

import threading
import time

import zmq
from zmq.utils.monitor import recv_monitor_message

from random import randrange

print("Current libzmq version is %s" % zmq.zmq_version())
print("Current  pyzmq version is %s" % zmq.__version__)
if zmq.zmq_version_info() < (4, 0):
    raise RuntimeError("monitoring in libzmq version < 4.0 is not supported")

EVENT_MAP = {}
print("Event names:")
for name in dir(zmq):
    if name.startswith('EVENT_'):
        value = getattr(zmq, name)
        print("%21s : %4i" % (name, value))
        EVENT_MAP[value] = name


# Thread code that will keep monitoring for events on the monitor
def event_monitor(monitor):
    while monitor.poll():
        evt = recv_monitor_message(monitor)
        evt.update({'description': EVENT_MAP[evt['event']]})
        print("Event: {}".format(evt))
        if evt['event'] == zmq.EVENT_MONITOR_STOPPED:
            break
    monitor.close()
    print()
    print("event monitor thread done!")

context = zmq.Context()

# The difference here is that this is a publisher and its aim in life is
# to just publish some value. The binding is as before.
socket = context.socket(zmq.PUB)
monitor = socket.get_monitor_socket ()

# start a thread for monitoring
t = threading.Thread(target=event_monitor, args=(monitor,))
t.start()

# Publisher binds on this socket
socket.bind("tcp://*:5556")

# keep publishing 
while True:
    zipcode = randrange(1, 100000)
    temperature = randrange(-80, 135)
    relhumidity = randrange(10, 60)

    socket.send_string("%i %i %i" % (zipcode, temperature, relhumidity))
