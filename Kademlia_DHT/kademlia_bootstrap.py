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

# our DHT modularized code
from kademlia_dht import Kademlia_DHT

###################################
#
# Parse command line arguments
#
###################################
def parseCmdLineArgs ():
    # instantiate a ArgumentParser object
    parser = argparse.ArgumentParser (description="Kademlia bootstrapping")

    # Now specify all the optional arguments we support
    parser.add_argument ("-c", "--create", default=False, action="store_true", help="Create a new DHT ring, otherwise we join a DHT") 
    parser.add_argument ("-d", "--debug", default=logging.WARNING, action="store_true", help="Logging level (see logging package): default WARNING else DEBUG")
    parser.add_argument ("-i", "--ipaddr", type=str, default=None, help="IP address of any existing DHT node")
    parser.add_argument ("-p", "--port", help="port number used by one or more DHT nodes", type=int, default=8468)
    parser.add_argument ("-o", "--override_port", help="overriden port number used by our node. Used if we want to create many nodes on the same host", type=int, default=None)

    return parser.parse_args()


###################################
#
# Main program
#
###################################
def main ():
    # first parse the arguments
    print ("Main: parse command line arguments")
    args = parseCmdLineArgs ()

    # instantiate the DHT class
    print ("Main: Instantiate the Kademlia DHT object")
    if (args.create):
        kdht = Kademlia_DHT (True)
    else:
        kdht = Kademlia_DHT ()
        

    # initialize the object
    print ("Main: Initialize the Kademlia DHT object")
    if (not kdht.initialize (args)):
        print ("Main: Initialization of Kademlia DHT failed")
        return
    
    # check if this is the first node of the ring or others joining
    # an existing one
    if (args.create):
        print ("Main: create the first DHT node")
        kdht.create_bootstrap_node ()
    else:
        print ("Main: join some DHT node")
        kdht.connect_to_bootstrap_node ()


###################################
#
# Main entry point
#
###################################
if __name__ == "__main__":
    main()
