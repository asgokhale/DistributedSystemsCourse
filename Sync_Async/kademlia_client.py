# Author: Aniruddha Gokhale
# Vanderbilt University
# Created: Feb 2022
# 
# Code based on sample available at https://github.com/bmuller/kademlia
#
# This code is modified from the original by making some values more
# configurable instead of hard-coded.  Moreover, it has been integrated
# with ZeroMQ-based code
#
#

import sys
import os
import logging     # for debug output
import asyncio     # the Kademlia library uses the asynchronous I/O

from kademlia.network import Server  # this is a higher level class

import json

##################################################################
class Kademlia_Client ():
    """Maintains the local details of the instantiated DHT"""

    # constructor 
    def __init__ (self, args):
        self.my_port = args.queryport  # port num used by this node
        self.bootstrap_ipaddr = args.dhtaddr  # IP addr of existing DHT node used to bootstrap to
        self.bootstrap_port = args.dhtport  # port num existing DHT node used to bootstrap to
        self.logger = logging.getLogger ('Sync_Async') # singleton logging instance

        # initialize the server object
        self.server = Server ()

        # initialize underlying logger
        handler = logging.StreamHandler () 
        formatter = logging.Formatter ('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter (formatter)
        self.logger.addHandler (handler)
        self.logger.setLevel (args.debug)

        print ("Kademlia_DHT::__init__ - My port = {}, Bootstrap port = {}, Bootstrap IP Addr = {}".format (self.my_port, self.bootstrap_port, self.bootstrap_ipaddr))
        
    ######################################
    # ExecuteFileStrategy
    ######################################
    async def ExecuteFileStrategy (self):
        """ Execute file strategy"""
        # Here we wait for the zmq side to create this rendezvous
        # object, which is a file. We read from it, which will be
        # list of topics to look up. We obtain all these results,
        # store them in a dictionary and write it into another
        # rendezvous object (in our case another file) for the
        # zmq side to read it.

        # Now wait for the other side to send us its file that has
        # the reply
        print ("Kademlia_Client::ExecuteFileStrategy - wait for query file")
        while (not os.path.exists ("/tmp/zmqquery.json")):
            # busy waiting
            time.sleep (1)

        print ("Kademlia_Client::ExecuteFileStrategy - open the query file")
        with open ("/tmp/zmqquery.json", "r") as fp:
            # read file
            query = json.load (fp)

        print ("Kademlia_Client::ExecuteFileStrategy - received query is {}".format (query))

        # Now we delete what the ZMQ side created as
        # we have used it and this way the other
        # side need not worry as to whether we have
        # seen the file or not and clean it.
        os.unlink ("/tmp/zmqquery.json")

        # This query will be of the form {"topic": [list of topics]}
        # For each such topic, we ask our async part to get the info
        response = {}  # start with an empty dictionary
        print ("Kademlia_Client::ExecuteFileStrategy - obtaining value for keys {}".format (query["topics"]))

        response = await self.get_value (self.my_port, query["topics"])

        # once all keys are obtained, we store these results
        # in a jsonified form and essentially signal the other side
        with open ("/tmp/dhtresponse.json", "w") as fp:
            json.dump (response, fp)

        fp.close ()
            
    ######################################
    # get value for the supplied key
    ######################################
    async def get_value (self, port, keys):
        print ("Kademlia_Client::get_value -- lookup key = {} on my port {}".format (keys, port))
        await self.server.listen (port)
        bootstrap_node = (self.bootstrap_ipaddr, int (self.bootstrap_port))
        print ("Kademlia_Client::get_value -- bootstrapping to {}".format (bootstrap_node))
        await self.server.bootstrap ([bootstrap_node])
        # we noticed that starting multiple listens is not
        # the right approach as it results in either port
        # already in use error and even if we change to
        # diff port, it possibly results in too many
        # concurrent requests causing extreme delays
        # Thus, a simpler and fast way is to serialize things
        # by having one connection and make requests one
        # after the other.
        result = {}  # this is our dictionary for the results
        for key in keys:  # we expect one or more search keys
            result[key] = await self.server.get (key)
        self.server.stop ()
        return result

