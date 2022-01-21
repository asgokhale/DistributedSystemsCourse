##############################################
#
# Author: Aniruddha Gokhale
#
# Created: Spring 2022
#
# Purpose: demonstrate a basic message passing server
#
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
    parser = argparse.ArgumentParser (description="Message Passing Server")

    # Now specify all the optional arguments we support

    # server's port
    parser.add_argument ("-p", "--port", default="5557", help="Port number used by message passing server, default: 5557")

    return parser.parse_args()


##################################
#
#  message handler
#
##################################
def handle_message (socket):
    # first thing is to receive whatever was received
    str = socket.recv_string ()
    print ("Handle the incoming message: {}".format (str))

    # check if the first characters are 
    if (str.find ("GET ") == 0):
        print ("Received a GET message, responding with what we received")
        # Technically, we could have looked up in a database for the received key
        # and sent the value but here we don't care. We just want to send something
        # back. So we send the same string we got
        socket.send_string (str)
    elif (str.find ("PUT ") == 0):
        print ("Received a PUT message, responding with what we received")
        # Technically, we could have looked up in a database for the received key
        # and modifed its value or inserted a new record but here we don't care.
        # We just want to send something back. So we send the same string we got
        socket.send_string (str)
    else:
        print ("Unrecognized message type")
        socket.send_string ("Sorry, unrecognized command")
        
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
    print ("Acquire the context object")
    context = zmq.Context()

    # Get a poller object. Here we use a poller so that it can notify us of
    # an incoming event.
    print ("Acquire the poller object")
    poller = zmq.Poller ()
    
    # Now create the right kind of socket
    print ("Get a REP socket for the server")
    socket = context.socket (zmq.REP)

    # now bind to the address
    bind_str = "tcp://*:" + args.port
    print ("Binding the message passing server at {}".format (bind_str))
    socket.bind (bind_str)

    # register with the poller
    print ("register with the poller for incoming requests")
    poller.register (socket, zmq.POLLIN)

    # Now just wait for events to occur (forever)
    print ("Running the event loop")
    while True:
        print ("Wait for the next event")
        events = dict (poller.poll ())

        # we are here means something showed up.  Make sure that the
        # event is on the registered socket
        if (socket in events):
            print ("Message arrived on our socket; so handling it")
            handle_message (socket)
        else:
            print ("Message is not on our socket; so ignoring it")
            
    

    

###################################
#
# Main entry point
#
###################################
if __name__ == "__main__":
    main ()
    
