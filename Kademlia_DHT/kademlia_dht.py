# Author: Aniruddha Gokhale
# Vanderbilt University
# Created: Jan 2022
# 
# Code based on sample available at https://github.com/bmuller/kademlia
#
# This code is slightly modified from the original by making some values more
# configurable instead of hard-coded.  For instance, the first node to start the
# Kademlia ring would forcibly listen on a port while the joining nodes on a different
# port.  However, we would like configurability since we want to possibly run these
# nodes in bulk say in a Kubernetes cluster or on Mininet.  Moreover, we make it
# more cleaner and modular so that aspects of it can be reused in other parts,
# e.g., assignments for the Distributed Systems class.
#
#
# Here, we define a class for the DHT

import logging     # for debug output
import asyncio     # the Kademlia library uses the asynchronous I/O

from kademlia.network import Server  # this is a higher level class

class Kademlia_DHT ():
    """Maintains the local details of the instantiated DHT"""

    # constructor 
    def __init__ (self, create=False):
        self.create = create # are we creating a DHT or bootstrapping to (default)
        self.server = None # This node (could be the bootstrap node)
        self.logger = logging.getLogger ('kademlia') # singleton logging instance
        self.my_port = None  # port num used by this node
        self.bootstrap_ipaddr = None  # IP addr of some other DHT node used to bootstrap to
        self.bootstrap_port = None  # port num used by some other DHT node used to bootstrap to

    # initialization
    def initialize (self, args):
        # make sure that if we are joining a DHT ring, there should
        # be an IP address supplied for the bootstrap node
        if (not self.create and args.ipaddr is None):
            print ("Kademlia_DHT::initialize - IP address for bootstrap node is not provided. Giving up")
            return False

        # set the bootstrap IP addr (if any)
        self.bootstrap_ipaddr = args.ipaddr
        
        # set the values of bootstrap port and my port
        if (args.override_port is None):
            # we did not override the port
            self.bootstrap_port = args.port
            self.my_port = args.port
        else:
            # we overrode the port
            self.bootstrap_port = args.port
            self.my_port = args.override_port

        print ("Kademlia_DHT::initialize - My port = {}, Bootstrap port = {}, Bootstrap IP Addr = {}".format (self.my_port, self.bootstrap_port, self.bootstrap_ipaddr))
        
        # initialize the server object
        self.server = Server ()

        # initialize underlying logger
        handler = logging.StreamHandler () 
        formatter = logging.Formatter ('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter (formatter)
        self.logger.addHandler (handler)
        self.logger.setLevel (args.debug)

        return True

    ######################################
    # DHT is already created; just join one any one of the nodes
    ######################################
    def connect_to_bootstrap_node (self):
        loop = asyncio.get_event_loop ()
        loop.set_debug (True)

        loop.run_until_complete (self.server.listen (self.my_port))
        bootstrap_node = (self.bootstrap_ipaddr, int (self.bootstrap_port))
        loop.run_until_complete (self.server.bootstrap ([bootstrap_node]))

        try:
            loop.run_forever ()
        except KeyboardInterrupt:
            pass
        finally:
            self.server.stop ()
            loop.close ()


    ###################################
    # This is the first node of this DHT ring
    ###################################
    def create_bootstrap_node (self):
        loop = asyncio.get_event_loop ()
        loop.set_debug (True)

        loop.run_until_complete (self.server.listen (self.my_port))

        try:
            loop.run_forever ()
        except KeyboardInterrupt:
            pass
        finally:
            self.server.stop ()
            loop.close ()

    ######################################
    # set key value
    ######################################
    async def set_value (self, key, value):
        await self.server.listen (self.my_port)
        bootstrap_node = (self.bootstrap_ipaddr, int (self.bootstrap_port))
        await self.server.bootstrap ([bootstrap_node])
        await self.server.set (key, value)
        self.server.stop ()

    ######################################
    # get value for the supplied key
    ######################################
    async def get_value (self, key):
        await self.server.listen (self.my_port)
        bootstrap_node = (self.bootstrap_ipaddr, int (self.bootstrap_port))
        await self.server.bootstrap ([bootstrap_node])
        result = await self.server.get (key)
        self.server.stop ()
        return result

