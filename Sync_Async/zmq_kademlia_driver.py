# Sample code for CS6381
# Vanderbilt University
# Instructor: Aniruddha Gokhale
# Created: Spring 2022
#
#
# Purpose:
# Demonstrate the integration of the ZMQ server capabilities,
# which uses synchronous communication via the REQ-REP pattern,
# with Kademlia's client-side capabilities (set and get), which
# use async I/O
#
# The goal is to use multiple different approaches in one single
# code base. Strategies include:
# (a) out-of-band file used as a rendezvous point between the
#     sync and async parts of the code where we need to run this
#     same code as two separate processes
# (b) multiple processes that 
# (c) 

import sys  # system library
import argparse   # for argument parsing
import logging     # for debug output

# for child processes
import subprocess

# our zmq side library
import zmq_server as zs

# our kademlia side library
import kademlia_client as kc

# asyncio
import asyncio

########################################################
#
#  The main driver class representing the parent role
#
########################################################
class Driver ():
    """ Driver program """

    # constructor
    def __init__ (self, args):
        self.args = args

    # Execute the strategy. Here we have large number of cases
    # to cover and it depends on whether this was the top-level
    # parent process (for multi process and multi threaded cases)
    async def ExecuteStrategy (self):
        # Now, depending on the role (parent or one of the
        # children: zmq or kademlia), we take appropriate action
        if (self.args.role == "parent"):
            # we are the parent process
            print ("Driver::ExecuteStrategy - parent role")

            # now handle the diff strategies
            if (self.args.strategy == "file" or self.args.strategy == "ipc"):
                print ("Driver::ExecuteStrategy - file or ipc strategy used")
                self.ExecuteProcessBasedStrategy ()
            elif (self.args.strategy == "thread"):
                pass
            elif (self.args.strategy == "combined"):
                await self.ExecuteCombinedStrategy ()
            else:
                # we should never be here as arg parsing will catch the error
                print ("Driver: unknown role {}".format (args.role))
                raise

        # ZMQ role
        elif (self.args.role == "zmq"):
            print ("Driver::ExecuteStrategy - this is the zmq child process")
            # now handle the diff strategies
            if (self.args.strategy == "file"):
                # Here we execute the ZMQ Client
                self.ExecuteZMQFileStrategy ()
            elif (self.args.strategy == "ipc"):
                pass
            elif (self.args.strategy == "thread"):
                pass
            elif (self.args.strategy == "combined"):
                pass
            else:
                # we should never be here as arg parsing will catch the error
                print ("Driver: unknown role {}".format (args.role))
                raise

        # Kademlia role
        elif (self.args.role == "kademlia"):
            print ("Driver::ExecuteStrategy - this is the kademlia child process")
            # now handle the diff strategies
            if (self.args.strategy == "file"):
                # Here we execute the DHT Client
                await self.ExecuteDHTFileStrategy ()
            elif (self.args.strategy == "ipc"):
                pass
            elif (self.args.strategy == "thread"):
                pass
            elif (self.args.strategy == "combined"):
                pass
            else:
                # we should never be here as arg parsing will catch the error
                print ("Driver: unknown role {}".format (args.role))
                raise
            
        else:
            # we should never here because argument parsing will
            # throw the error and exit
            print ("Driver: unknown role {}".format (args.role))
            raise

    ###########################################################
    # execute the process based strategies (file or ipc).
    ###########################################################
    def ExecuteProcessBasedStrategy (self):
        # This code will be executed by the Parent process
        #
        # here we will create two child processes: one for
        # the ZMQ server and one for the Kademlia client
        # They will talk to each other either via an
        # external file or traditional IPC like a pipe

        # construct the command lines to run the zmq and kademlia
        # child processes, which will then communicate
        print ("Driver: construct the command lines to start child processes")
        zmq_cmdlineargs = ["python3", "zmq_kademlia_driver.py", "-z", str (self.args.zmqport), "zmq", self.args.strategy]
        dht_cmdlineargs = ["python3", "zmq_kademlia_driver.py", "-i", self.args.dhtaddr, "-p", str (self.args.dhtport), "-q", str (self.args.queryport), "kademlia", self.args.strategy]

        print ("Driver::ExecuteProcessBasedStrategy - command line args are {} and {}".format (zmq_cmdlineargs, dht_cmdlineargs))

        zmqChild = subprocess.run (zmq_cmdlineargs, capture_output=True)
        dhtChild = subprocess.run (dht_cmdlineargs, capture_output=True)

        print ("ZMQ Child output = {}".format(zmqChild.stdout))
        print ("DHT Child output = {}".format(dhtChild.stdout))

    ################################################
    # execute the ZMQ-side file strategy.
    #############################################
    def ExecuteZMQFileStrategy (self):
        # This code will be executed by the ZMQ child process
        server = zs.ZMQ_Server (self.args)
        server.ExecuteFileStrategy ()

    #############################################
    # execute the Kademlia-side file strategy.
    #############################################
    async def ExecuteDHTFileStrategy (self):
        # This code will be executed by the DHT child process
        client = kc.Kademlia_Client (self.args)
        await client.ExecuteFileStrategy ()
        
    ###########################################################
    # execute the combined strategy
    ###########################################################
    async def ExecuteCombinedStrategy (self):
        # here we execute a combined strategy where the async
        # block encapsulates the sync block

        # first, instantiate the ZMQ and Kademlia objects
        print ("Driver::ExecuteCombinedStrategy -- instantiate objects")
        server = zs.ZMQ_Server (self.args)
        client = kc.Kademlia_Client (self.args)

        print ("Driver::ExecuteCombinedStrategy - receive query")
        query = server.socket.recv_json ()
        print ("Driver::ExecuteCombinedStrategy - received query {}".format (query))
        response = {}  # start with an empty dictionary
        i = 0
        #for key in query["topics"]:
            #print ("Driver::ExecuteCombinedStrategy - obtaining value for key {}".format (key))
            # response[key] = await client.get_value (client.my_port+i, key)
            #    i = i + 1

        print ("Driver::ExecuteCombinedStrategy - obtaining value for keys {}".format (query["topics"]))
        response = await client.get_value (client.my_port, query["topics"])
        print ("Driver::ExecuteCombinedStrategy - sending response {}".format (response))
        server.socket.send_json (response)
        
###################################
#
# Parse command line arguments
#
###################################
def parseCmdLineArgs ():
    # instantiate a ArgumentParser object
    parser = argparse.ArgumentParser (description="ZMQ-Kademlia Integration for Sync-AsyncDemo")

    # Now specify all the optional arguments we support

    # used by logger
    parser.add_argument ("-d", "--debug", default=logging.WARNING, action="store_true", help="Logging level (see logging package): default WARNING else DEBUG")
    
    # this is used to reach the DHT node's IP address
    parser.add_argument ("-i", "--dhtaddr", type=str, default="10.0.0.1", help="IP address of some DHT node, default 10.0.0.1 in Mininet")

    # this is the port number used by DHT node that we want to reach
    parser.add_argument ("-p", "--dhtport", help="port number used by Kademlia DHT node, default=8468", type=int, default=8468)

    # As a querying client of the DHT, we also need a port
    parser.add_argument ("-q", "--queryport", help="port number used by Kademlia query client, default=8877", type=int, default=8877)

    # We need a port for the ZMQ server side
    parser.add_argument ("-z", "--zmqport", help="port number used by ZMQ server, default=5557", type=int, default=5557)

    # what role are we playing
    parser.add_argument ("role", choices=["parent", "zmq", "kademlia"])

    # what strategy are we using
    parser.add_argument ("strategy", choices=["file", "ipc", "thread", "combined"])
    
    return parser.parse_args ()

#####################################################################
#
#  Main program
#
#####################################################################

async def main ():
    # first parse the arguments
    print ("Main: parse command line arguments")
    args = parseCmdLineArgs ()

    # instantiate a driver object
    print ("Main: instantiating the driver object")
    driver = Driver (args)

    # execute the strategy
    print ("Main: driver executing the appropriate strategy")
    await driver.ExecuteStrategy ()
    

###################################
#
# Main entry point
#
###################################
if __name__ == "__main__":

    asyncio.run (main ())

