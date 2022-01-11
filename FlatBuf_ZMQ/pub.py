#  Author: Aniruddha Gokhale
#  Created: Fall 2019
#  Modified: Spring 2021
#
#  Purpose: demonstrate publishing of topic data type using flatbuffers
#
#  Here our topic comprises a sequence number, a timestamp, and a data buffer
#  of several uint32 numbers (whose value is not relevant to us)

# The different packages we need in this Python sample code
import os
import sys
import time
import serialize as sz  # this is the package we have defined in the file serialize.py
import zmq

# This is the main method
def main ():
    # change these params or add command line parsing to modify these
    # hard coded values
    num_iters = 1000   # we are going to send the data these many times
    vec_len = 5  # this is the length of our vector we are going to send
    
    print ("Publisher main program")

    # first get the zmq context, which is the first action before we can use ZMQ
    print ("Get zmq context")
    ctx = zmq.Context ()

    # now get a PUB socket because this code will serve as a publisher
    print ("Get zmq context")
    socket = ctx.socket (zmq.PUB)

    # now bind this socket to a well known port (default)
    print ("bind the socket")
    socket.bind ("tcp://*:5556")

    # now publish our information for the number of desired iterations
    for i in range (num_iters):
        # get a serialized buffer with seq num and some data items
        print ("Iteration #{}".format (i))
        print ("serialize the topic")

        # here we are calling our serialize method passing it
        # the iteration number, the topic identifier, and length.
        # The underlying method creates some dummy data, fills
        # up the data structure and serializes it into the buffer
        buf = sz.serialize (i, "DATA", vec_len)

        # let the publisher just publish this
        print ("send the topic")
        socket.send (buf)

        # sleep a while before we send the next data
        print ("sleep for 50 msec")
        time.sleep (0.050)  # 50 msec

    # now serialize a special topic called END 
    print ("Iteration #{}".format (num_iters+1))
    print ("serialize the final packet")
    buf = sz.serialize (num_iters+1, "END", 0)

    # let the publisher just publish this
    print ("send the final sample to tell subscriber we are done")
    socket.send (buf)
    
if __name__ == '__main__':
    main()
