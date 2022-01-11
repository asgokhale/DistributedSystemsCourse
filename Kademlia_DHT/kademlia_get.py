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


import argparse   # for argument parsing
import logging     # for debug output
import asyncio     # the Kademlia library uses the asynchronous I/O

# our DHT modularized code
from kademlia_dht import Kademlia_DHT

###################################
#
# Parse command line arguments
#
###################################
def parseCmdLineArgs ():
    # instantiate a ArgumentParser object
    parser = argparse.ArgumentParser (description="Kademlia set value")

    # Now specify all the optional arguments we support
    parser.add_argument ("-d", "--debug", default=logging.WARNING, action="store_true", help="Logging level (see logging package): default WARNING else DEBUG")
    parser.add_argument ("-i", "--ipaddr", type=str, default=None, help="IP address of any existing DHT node")
    parser.add_argument ("-p", "--port", help="port number used by one or more DHT nodes", type=int, default=8468)
    parser.add_argument ("-o", "--override_port", help="overriden port number used by our node. Used if we want to create many nodes on the same host", type=int, default=None)

    # add positional argument. which is the key
    parser.add_argument ("key", type=str, help="Key to get the value under it")
    
    return parser.parse_args ()

###################################
#
# Main program (here we are making it an async function
#
###################################
async def main ():
    # first parse the arguments
    print ("Main: parse command line arguments")
    args = parseCmdLineArgs ()

    # instantiate the DHT class
    print ("Main: Instantiate the Kademlia DHT object")
    kdht = Kademlia_DHT ()

    # initialize the object
    print ("Main: Initialize the Kademlia DHT object")
    if (not kdht.initialize (args)):
        print ("Main: Initialization of Kademlia DHT failed")
        return
    
    # now set the value
    print ("Main: Bootstrap and key value for key")
    result = await kdht.get_value (args.key)

    print ("Main: returned result for key = {} is {}".format (args.key, result))

###################################
#
# Main entry point
#
###################################
if __name__ == "__main__":
    asyncio.run (main ())

