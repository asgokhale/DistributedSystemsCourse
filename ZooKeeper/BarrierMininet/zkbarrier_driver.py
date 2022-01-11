#!/usr/bin/python
#  
#
# Vanderbilt University Computer Science
# Author: Aniruddha Gokhale
# Course: CS 6381 Distributed Systems Principles
# Created: Spring 2018
#
# Purpose: Demonstrate Zookeeper Barrier Synchronization inside Mininet
#
# Code builds on the single process threaded version but here each
# client is a process on its own and runs on a host of Mininet. 
#
# This is the Driver program
#
# Approach:
#
# We maintain a driver program which creates a "/barrier" znode
# and maintains a count of how many children nodes it has noticed appear
# under the tree.
#
# A client is implemented as a thread. Its job in life is to create a child
# node under "/barrier" with its thread name and wait to see what is the
# value maintained by the parent znode. The moment the number reaches the
# barrier value, the client declares success and proceeds to do its work
# which here is pretty much nothing and then exits. Because it creates a
# ephemeral node, when the client exits, its znode is automatically
# deleted by ZooKeeper.
#
# In the meantime, after all client threads have exited, the driver will
# cleanup its znode and then disconnect from ZooKeeper and then exit.
#

# system and time
import os
import sys
import time

# argument parser
import argparse

# Now import the kazoo package that supports Python binding
# to ZooKeeper
from kazoo.client import KazooClient

# to avoid any warning about no handlers for logging purposes, we
# do the following but there is some exception getting thrown so for
# now I am commenting this out.
import logging
logging.basicConfig ()

# ------------------------------------------------------------------
# The driver class. Does not derive from anything
#
class ZK_Driver ():
    """ The ZooKeeper Driver Class """

    #################################################################
    # constructor
    #################################################################
    def __init__ (self, args):
        self.zkIPAddr = args.zkIPAddr  # ZK server IP address
        self.zkPort = args.zkPort # ZK server port num
        self.numClients = args.numClients # used as barrier condition
        self.zk = None  # session handle to the server
        self.path = "/barrier" # refers to the znode path being manipulated
        self.barrier = False

    #-----------------------------------------------------------------------
    # Debugging: Dump the contents

    def dump (self):
        """dump contents"""
        print ("=================================")
        print(("Server IP: {}, Port: {}; Path = {}, NumClients = {}".format (self.zkIPAddr, self.zkPort, self.path, self.numClients)))
        print ("=================================")

    # -----------------------------------------------------------------------
    # Initialize the driver
    def init_driver (self):
        """Initialize the client driver program"""

        try:
            # debug output
            self.dump ()

            # instantiate a zookeeper client object
            # right now only one host; it could be the ensemble
            hosts = self.zkIPAddr + str (":") + str (self.zkPort)
            print(("Driver::init_driver -- instantiate zk obj: hosts = {}".format(hosts)))
            self.zk = KazooClient (hosts)
            print(("Driver::init_driver -- state = {}".format (self.zk.state)))
            
        except:
            print("Unexpected error in init_driver:", sys.exc_info()[0])
            raise

    
    # -----------------------------------------------------------------------
    # Run the driver
    #
    # Our logic is such that we first create the znode with value 0
    # Then we create the application threads. Each thread creates a child
    # node under the main znode, which should notify the driver. Everytime
    # the driver is notified, it will update the value in the znode
    # At the same time, the threads are waiting on the znode's value. The
    # moment they see the barrier reached, they declare victory :-)
    # -----------------------------------------------------------------------
    def run_driver (self):
        """The actual logic of the driver program """


        # first connect to the zookeeper server
        print ("Driver::run_driver -- connect with server")
        self.zk.start ()
        print(("Driver::run_driver -- state = {}".format (self.zk.state)))

        # next, create a znode for the barrier sync with initial value 0
        print ("Driver::run_driver -- create a znode for barrier")
        self.zk.create (self.path, value=b"0")

        #-----------------------------------------------------------
        # this is the watcher callback that gets invoked when
        # children get added to the
        #
        # Notice how this is a nested call
        @self.zk.ChildrenWatch (self.path)
        def child_change_watcher (children):
            """Children Watcher"""
            print(("Driver::run -- children watcher: num childs = {}".format (len (children))))

            # every time we get the num of children, we set the value
            # of the metadata to be the number of children received
            if self.zk.exists (self.path):
                # this better be the case
                # so now update the znode value to reflect the
                # number of children (only when value > 0). This should
                # trigger the watch for our clients who are watching
                # the data

                if (len (children) > 0):
                    print(("Driver::child_change_watcher - setting new value for children = {}".format (len(children))))
                    self.zk.set (self.path, str (len (children)).encode ())

                # has the number of children reached the barrier condition?
                if (self.numClients == len (children)):
                    self.barrier = True

            else:
                print ("Driver:run_driver -- child watcher -- znode does not exist")
        #-----------------------------------------------------------

        print ("Driver::run_driver -- wait for the clients to reach barrier")

        while (self.barrier == False):
            time.sleep (1)
            
        # Now wait till all our children znodes are gone. They were ephemeral
        # and so after the client disconnects, that znode is gone.
        print ("Driver::run_driver -- now wait for clients to remove their znodes")
        while (True):
            # here we are sure our node exists
            value, stat = self.zk.get (self.path)
            if (stat.children_count == 0):
                # all child znodes are gone so get out of the loop
                print ("Driver::run_driver -- all client znodes are gone")
                break
                
        print(("Driver::run_driver -- now remove the znode {}".format (self.path)))
        self.zk.delete (self.path, recursive=True)
        
        print ("Driver::run_driver -- disconnect and close")
        self.zk.stop ()
        self.zk.close ()

        print ("Driver::run_driver -- Bye Bye")
        
##################################
# Command line parsing
##################################
def parseCmdLineArgs ():
    # parse the command line
    parser = argparse.ArgumentParser ()

    # add optional arguments
    parser.add_argument ("-a", "--zkIPAddr", default="127.0.0.1", help="ZooKeeper server ip address, default 127.0.0.1")
    parser.add_argument ("-c", "--numClients", type=int, default=5, help="Number of client apps in the barrier, default 5")
    parser.add_argument ("-p", "--zkPort", type=int, default=2181, help="ZooKeeper server port, default 2181")
    
    # add positional arguments in that order
    # parser.add_argument ("addrfile", help="File of host ip addresses")

    # parse the args
    args = parser.parse_args ()

    return args
    
#------------------------------------------
# main function
def main ():
    """ Main program """

    print("Demo program for ZooKeeper-based Barrier Sync")
    parsed_args = parseCmdLineArgs ()
    
    # 
    # invoke the driver program
    driver = ZK_Driver (parsed_args)

    # initialize the driver
    driver.init_driver ()
    
    # start the driver
    driver.run_driver ()

#----------------------------------------------
if __name__ == '__main__':
    main ()
