##############################################
#
# Author: Aniruddha Gokhale
#
# Created: Spring 2022
#
# Purpose: demonstrate a basic message passing client
#
##############################################

import argparse   # for argument parsing
import zmq  # ZeroMQ 

###################################
#
# Parse command line arguments
#
###################################
def parseCmdLineArgs ():
    # instantiate a ArgumentParser object
    parser = argparse.ArgumentParser (description="Message Passing Client")

    # Now specify all the optional arguments we support

    # server's IP address
    parser.add_argument ("-a", "--ipaddr", default="localhost", help="IP address of the message passing server, default: localhost")

    # server's port
    parser.add_argument ("-p", "--port", default="5557", help="Port number used by message passing server, default: 5557")

    return parser.parse_args()


##################################
#
#  main program
#
##################################
def main ():
    # first parse the arguments
    print ("Main: parse command line arguments")
    args = parseCmdLineArgs ()

    print ("Current libzmq version is %s" % zmq.zmq_version())
    print ("Current  pyzmq version is %s" % zmq.__version__)
    
    # In ZeroMQ, the first thing we do is get a context
    context = zmq.Context()

    # Now create the right kind of socket
    print ("Get a REQ socket")
    socket = context.socket (zmq.REQ)

    # now connect to the message passing server
    connect_str = "tcp://" + args.ipaddr + ":" + args.port
    print ("Connecting to message passing server at {}".format (connect_str))
    socket.connect (connect_str)

    # Now send 4 messages, two valid, two invalid.
    # For each one, we create a message and send it
    #
    # Say, in our system, only 2 types of messages are allowed: GET and PUT,
    # and there is a strict format where the message type must be in
    # uppercase followed by a single space and then some additional info.
    # Any deviation and the receiving party will not understand it.
    #
    # Note how the sender needs to create a message and ensure that
    # it is constructed in the correct manner. Moreover, if we create a 
    # malformed packet, the other side is not going to understand.
    #
    # We demonstrate these cases below.
    #
    print ("Sending a valid GET message")
    socket.send_string ("GET foo")
    reply = socket.recv_string ()
    print ("Received reply = {}".format (reply))
    
    print ("Sending a malformed GET message (no space after GET)")
    socket.send_string ("GETfoo")
    reply = socket.recv_string ()
    print ("Received reply = {}".format (reply))
    
    print ("Sending a valid PUT message")
    socket.send_string ("PUT foo bar")   # a key-value
    reply = socket.recv_string ()
    print ("Received reply = {}".format (reply))

    print ("Sending a POST message (which is not a known message type)")
    socket.send_string ("POST junk")
    reply = socket.recv_string ()
    print ("Received reply = {}".format (reply))

    print ("Message Passing client is exiting")
    
###################################
#
# Main entry point
#
###################################
if __name__ == "__main__":
    main ()
    
