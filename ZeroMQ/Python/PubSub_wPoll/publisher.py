# Sample code for CS6381
# Vanderbilt University
# Instructor: Aniruddha Gokhale
#
# Code taken from ZeroMQ examples and modified to demonstrate
# a subscriber with multiple sockets and using poll to decide if
# there is incoming data.
#
# We can execute the code on localhost or in mininet
#
# Publisher will publish three diff kinds of topics: temp, humidity and pressure
#

import sys
import time
import zmq
from random import randrange

# obtain the context
context = zmq.Context()

# bind to all interfaces
bind_str = "tcp://*:5555"

# acquire a publisher type socket
print ("Publisher binding on all interfaces on port 5555")
socket = context.socket (zmq.PUB)
socket.bind (bind_str)

# keep publishing 
while True:
    # decide what topic type we are publishing
    category = randrange (1, 4)
    if category == 1:  # temp
        temp = randrange (-10, 101)
        topic = "temp:" + str (temp)
        # topic = "temp:70"  # this was hardcoded to test the reception on subscriber
    elif category == 2: # humidity
        humidity = randrange (20, 101)
        topic = "humidity:" + str (humidity)
        #topic = "humidity:50" # this was hardcoded to test the reception on subscriber
    elif category == 3: # pressure
        pressure = randrange (26, 34)
        topic = "pressure:" + str (pressure)
        #topic = "pressure:30" # this was hardcoded to test the reception on subscriber
    else:
        print ("bad category")
        continue

    print ("Sending: {}".format (topic))
    socket.send_string (topic)
    time.sleep (0.1)  # take a short break
