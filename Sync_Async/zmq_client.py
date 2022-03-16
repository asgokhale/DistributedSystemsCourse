# Sample code for CS6381
# Vanderbilt University
# Instructor: Aniruddha Gokhale
#
# Code taken from ZeroMQ examples with additional
# comments or extra statements added to make the code
# more self-explanatory  or tweak it for our purposes
#
# Moreover, we are using this as a sample code to mimic
# the zmq-based client-server interactions that happen
# when the publishers/subscribers in our programming
# assignments interact with the registry. 

import sys  # system library
import argparse   # for argument parsing
import logging     # for debug output

# zmq library
import zmq

# for timing
import time

###################################
#
# Parse command line arguments
#
###################################
def parseCmdLineArgs ():
    # instantiate a ArgumentParser object
    parser = argparse.ArgumentParser (description="ZMQ Client for Sync-AsyncDemo")

    # Now specify all the optional arguments we support
    parser.add_argument ("-i", "--ipaddr", type=str, default="localhost", help="IP address of ZMQ server, default localhost")
    parser.add_argument ("-p", "--port", help="port number used by ZMQ server, default=5557", type=int, default=5557)

    return parser.parse_args ()

#####################################################################
#
#  Main program
#
#####################################################################

def main ():
    # first parse the arguments
    print ("Main: parse command line arguments")
    args = parseCmdLineArgs ()

    # To use ZMQ, every session needs this singleton context object
    print ("Open a zmq context")
    context = zmq.Context()

    # create a socket of type REQ
    print ("Create a REQ socket")
    socket = context.socket(zmq.REQ)

    # create the connection string
    connect_str = "tcp://" + args.ipaddr + ":" + str (args.port)
    print ("Connecting to {}".format (connect_str))
    socket.connect (connect_str)

    # Here we are emulating what our publishers/subscribers
    # will be doing when querying for information in DHT
    # registry. To that end, we just mock up some arbitrary
    # info in the form of keys that we are querying. Set
    # operations could be similar but here we are assuming
    # that 
    #
    # Here we have created some topics and some are not defined
    # in the system.
    query = {
        "topics": ["weather", "traffic", "airquality", "humidity", "foo", "bar"]

    }

    # send to server
    print ("Sending query {}".format (query))
    start_time = time.time ()
    socket.send_json (query)

    # now receive results
    results = socket.recv ()
    end_time = time.time ()
    print ("Received query results {}".format (results))
    print ("Query took {} time".format (end_time - start_time))


    # we are done
    print ("Ending the session")
    socket.close ()
    
###################################
#
# Main entry point
#
###################################
if __name__ == "__main__":
    print("Current libzmq version is %s" % zmq.zmq_version())
    print("Current  pyzmq version is %s" % zmq.__version__)

    main ()

