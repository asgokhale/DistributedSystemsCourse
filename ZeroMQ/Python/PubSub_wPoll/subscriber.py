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
#


import sys
import argparse   # argument parser
import zmq

class CS6381_Subscriber ():
    """ Subscriber class """

    #################################################################
    # constructor
    #################################################################
    def __init__ (self, args):
        # arguments
        self.addr = args.addr   # ip addr of publisher
        self.temp = args.temp # temperature we are interested in
        self.pressure = args.pressure  # pressure we are interested in
        self.humidity = args.humidity # humidity value we are interested in
        
        #  The zmq context
        self.context = None

        # we will use the poller to poll for incoming data
        self.poller = None
        
        # these are three sockets we open one for each subscription
        self.temp_socket = None
        self.pressure_socket = None
        self.humidity_socket = None

    #################################################################
    # configure the subscriber
    #################################################################
    def configure (self):

        # first get the context
        print ("Subscriber::configure - get the context object")
        self.context = zmq.Context()

        # obtain the poller
        print ("Subscriber::configure - get the poller object")
        self.poller = zmq.Poller ()

        # now let us obtain our sockets all of which are of SUB type
        print ("Subscriber::configure - obtain the three SUB sockets")
        self.temp_socket = self.context.socket (zmq.SUB)
        self.humidity_socket = self.context.socket (zmq.SUB)
        self.pressure_socket = self.context.socket (zmq.SUB)

        # connect all our sockets to the publisher
        print ("Subscriber::configure - connect the SUB sockets to publisher")
        connect_str = "tcp://" + self.addr + ":5555"
        self.temp_socket.connect (connect_str)
        self.humidity_socket.connect (connect_str)
        self.pressure_socket.connect (connect_str)
        
        # set filters on the sockets
        filter = "temp:" + self.temp
        print ("Subscriber:configure - subscribing to {}".format (filter))
        self.temp_socket.setsockopt_string(zmq.SUBSCRIBE, filter)
        filter = "humidity:" + self.humidity
        print ("Subscriber:configure - subscribing to {}".format (filter))
        self.humidity_socket.setsockopt_string(zmq.SUBSCRIBE, filter)
        filter = "pressure:" + self.pressure
        print ("Subscriber:configure - subscribing to {}".format (filter))
        self.pressure_socket.setsockopt_string(zmq.SUBSCRIBE, filter)
        
        # register these sockets for incoming data
        print ("Subscriber::configure - register our sockets with a poller")
        self.poller.register (self.temp_socket, zmq.POLLIN)
        self.poller.register (self.humidity_socket, zmq.POLLIN)
        self.poller.register (self.pressure_socket, zmq.POLLIN)

    #################################################################
    # run the event loop
    #################################################################
    def event_loop (self):
        print ("Subscriber:event_loop - run the event loop")
        while True:
            # poll for events. We give it an infinite timeout.
            # The return value is a socket to event mask mapping
            events = dict (self.poller.poll ())

            # find which socket was enabled and accordingly make a callback
            # Note that we must check for all the sockets since multiple of them
            # could have been enabled.
            if self.temp_socket in events:
                self.recv_temp ()
            
            if self.humidity_socket in events:
                self.recv_humidity ()
            
            if self.pressure_socket in events:
                self.recv_pressure ()
            
    #################################################################
    # receive temp
    #################################################################
    def recv_temp (self):
        string = self.temp_socket.recv_string()
        print ("Subscriber:recv_temp, value = {}".format (string))

    #################################################################
    # receive humidity
    #################################################################
    def recv_humidity (self):
        string = self.humidity_socket.recv_string()
        print ("Subscriber:recv_humidity, value = {}".format (string))

    #################################################################
    # receive pressure
    #################################################################
    def recv_pressure (self):
        string = self.pressure_socket.recv_string()
        print ("Subscriber:recv_pressure, value = {}".format (string))

##################################
# Command line parsing
##################################
def parseCmdLineArgs ():
    # parse the command line
    parser = argparse.ArgumentParser ()

    # add optional arguments
    parser.add_argument ("-a", "--addr", default="localhost", help="Publisher IP address, default localhost")
    parser.add_argument ("-t", "--temp", default="70", help="Temperature, default 70 F")
    parser.add_argument ("-p", "--pressure", default="30", help="Pressure, default 30")
    parser.add_argument ("-m", "--humidity", default="50", help="Humidity, default 50")
    
   # parse the args
    args = parser.parse_args ()

    return args
    
#################################################################
# main function
#################################################################
def main ():
    """ Main program """

    print("Current libzmq version is %s" % zmq.zmq_version())
    print("Current  pyzmq version is %s" % zmq.__version__)

    
    print ("Subscriber program")

    # first parse the arguments
    print ("Parse command line arguments")
    parsed_args = parseCmdLineArgs ()

    # instantiate the subscriber
    print ("Instantiate a subscriber object")
    subscriber =  CS6381_Subscriber (parsed_args)

    # configure the subscriber
    print ("Configure the subscriber")
    subscriber.configure ()

    # now let the subscriber wait in an event loop
    print ("Start the event loop")
    subscriber.event_loop ()

    print ("Subscriber event loop terminated")
    
#----------------------------------------------
if __name__ == '__main__':
    main ()
