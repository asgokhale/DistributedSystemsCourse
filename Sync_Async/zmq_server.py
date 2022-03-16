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
import os   # OS level features
import logging     # for debug output

# zmq library
import zmq

# JSON
import json

####################################################
#
#  The ZMQ server-side functionality
#
####################################################
class ZMQ_Server ():
    def __init__ (self, args):
        """ constructor """

        print("Current libzmq version is %s" % zmq.zmq_version())
        print("Current  pyzmq version is %s" % zmq.__version__)
        
        # create the context
        print ("ZMQ_Server::__init__ - creating context")
        self.context = zmq.Context ()

        # create a socket of type REP
        print ("ZMQ_Server::__init__ - creating REP socket")
        self.socket = self.context.socket (zmq.REP)

        # create the bind string
        bind_str = "tcp://*:" + str (args.zmqport)
        print ("ZMQ_Server::__init__ - binding the server to {}".format (bind_str))
        self.socket.bind (bind_str)


    # execute the file based strategy
    def ExecuteFileStrategy (self):
        """ File based strategy """

        # Now we get into a forever loop
        # while True:
        for i in range(1):
            # receive a query from the next client
            print ("ZMQ_Server::ExecuteFileStrategy - receive query")
            query = self.socket.recv_json ()
            print ("ZMQ_Server::ExecuteFileStrategy - received query {}".format (query))
            
            # since we are using the file-based approach, we now
            # create a file and dump this query into that file
            print ("ZMQ_Server::ExecuteFileStrategy - create and populate file")
            with open ("/tmp/zmqquery.json", "w") as fp:
                json.dump (query, fp)
                #fp.flush ()
                fp.close ()

            # Now wait for the other side to send us its file that has
            # the reply
            print ("ZMQ_Server::ExecuteFileStrategy - wait for response")
            while (not os.path.exists ("/tmp/dhtresponse.json")):
                # busy waiting
                time.sleep (1)

            with open ("/tmp/dhtresponse.json", "r") as fp:
                # read file
                response = json.load (fp)
                print ("ZMQ_Server::ExecuteFileStrategy - received response = {}".format (response))

                # send to the zmq client
                self.socket.send_json (response)

                # Now we delete what the DHT side created as
                # we have used it and this way the other
                # side need not worry as to whether we have
                # seen the file or not.
                os.unlink ("/tmp/dhtresp.json")
                
    
        # we are done
        print ("ZMQ_Server::Ending the ZMQ server session")
        self.socket.close ()
    
