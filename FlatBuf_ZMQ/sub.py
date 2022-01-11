#  Author: Aniruddha Gokhale
#  Created: Fall 2019
# Modified: Spring 2021
#
#  Purpose: demonstrate subscriber for a topic receiving complex data type
#
#  Here our topic comprises a sequence number, a timestamp, and a data buffer
#  of several uint32 numbers (whose value is not relevant to us)

# import the needed packages
import os
import sys
import time
import serialize as sz   # this is the serialization package we have in serialize.py file
import zmq  # for zeromq

# This is the main method
def main ():
    print ("Subscriber main program")

    # first get the zmq context
    print ("Get zmq context")
    ctx = zmq.Context ()

    # now get a SUB socket
    print ("Get SUB socket")
    socket = ctx.socket (zmq.SUB)

    # now bind this socket to a well know port (default)
    print ("Connect to publisher")
    socket.connect ("tcp://127.0.0.1:5556")

    # subscribe to a topic. By not providing any value to
    # setsockopt, we are going to accept everything from the
    # publisher
    print ("Subscribe to all topics")
    socket.setsockopt (zmq.SUBSCRIBE,  b"")
    
    # now receive the information
    while True:

        # receive a msg
        print ("Waiting to receive")
        buf = socket.recv ()
        
        # deserialize it (if it is the end, we get out)
        if (sz.deserialize (buf) == 0):
            break

        # Now we get latency and save to 
        
if __name__ == '__main__':
    main()
