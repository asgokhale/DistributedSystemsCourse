#
# Author: Aniruddha Gokhale
# Vanderbilt University
# CS 6381 Distributed Systems Principles
# Created: Spring 2018
# Modified: Spring 2019
#
# This is a sample code showing a variety of commands
# using a Python client for ZooKeeper. We assume that the
# ZooKeeper server is running.
#
# For now we are assuming the ZooKeeper server is on localhost

# import some basic packages just in case we need these
import os
import sys

# Now import the kazoo package that supports Python binding
# to ZooKeeper
from kazoo.client import KazooClient

# to avoid any warning about no handlers for logging purposes, we
# do the following but there is some exception getting thrown so for
# now I am commenting this out.
#import logging
#logging.basicConfig ()

# I had to move this code here so the variable zk is found below in the
# decorator. It has become somewhat ugly and will be cleaned up in the
# next iteration
print ("Instantiating a KazooClient object")
zk = KazooClient (hosts = "127.0.0.1:2181")
print ("client current state = {}".format (zk.state))

#*****************************************************************
# This is the watch callback function that is supposed to be invoked
# when changes get made to the znode of interest. Note that a watch is
# effective only once. So the client has to set the watch every time.
# To overcome the need for this, Kazoo has come up with a decorator.
# Decorators can be of two kinds: watching for data on a znode changing,
# and children on a znode changing
@zk.DataWatch("/foo")
def watch_data_change (data, stat):
    print ("\n*********** Inside watch_data_change *********")
    print ("Data changed for znode /foo: data = {}, stat = {}".format (data,stat))
    print ("*********** Leaving watch_data_change *********")

    
#*****************************************************************
# Effectively our main program
#
try:
    # instantiate a client object. Notice that we are assuming
    # that the server is on our localhost and at port 2181
    #
    # ZooKeeper clients go thru 3 states: LOST => when it is instantiated
    # or when not in a session with a server;
    # CONNECTED => when connected with server, and SUSPENDED => when the
    # connection is lost or the server node is no longer part of the
    # quorum
    #
    # In the following, we print the state of the client after every action
    # just to see what state we are in
    #
    # now connect to the server
    print ("Connecting to the ZooKeeper Server")
    zk.start ()
    print ("client current state = {}".format (zk.state))

    input ("Press any key to continue")

    # now start playing with the different commands

    # here we create a node just like we did via the CLI. But here we are
    # also showcasing the ephemeral attribute which means that the znode
    # will be deleted automatically by the server when the session is
    # terminated by this client
    print ("Creating an ephemeral znode /foo with value bar")
    zk.create ("/foo", value="bar", ephemeral=True, makepath=True)
    print ("client current state = {}".format (zk.state))

    input ("Press any key to continue")

    # Now we are going to check if the znode that we just created
    # exists or not. Note that a watch can be set on create, exists
    # and get/set methods
    print ("Checking if /foo exists (it better be)")
    if zk.exists ("/foo"):
        print ("/foo znode indeed exists")

        value,stat = zk.get ("/foo", watch=watch_data_change)
        print ("Details of /foo: value = {}, stat = {}".format (value, stat))
        
    else:
        print ("/foo znode does not exist, why?")
    
    input ("Press any key to continue")

    # Now let us change the data value on the /foo znode and see if
    # our watch gets invoked
    print ("Setting a new value on znode /foo")
    if zk.exists ("/foo"):
        print ("/foo znode still exists :-)")

        zk.set ("/foo", b"bar2")

        # Now see if the value was changed
        value,stat = zk.get ("/foo")
        print ("Details of /foo: value = {}, stat = {}".format (value, stat))
        
    else:
        print ("/foo znode does not exist, why?")
    
    input ("Press any key to continue")

    # now disconnect and we will notice that /foo gets deleted on the server
    print ("Disconnecting")
    zk.stop ()
    print ("client current state = {}".format (zk.state))

    input ("Press any key to continue")

    # Now reconnect to the server and see if our znode from the previous
    # session is still there
    print ("Reconnecting")
    zk.start ()
    print ("client current state = {}".format (zk.state))

    input ("Press any key to continue")

    print ("Checking if /foo still exists")
    if zk.exists ("/foo"):
        print ("/foo znode still exists -- not possible")
    else:
        print ("/foo znode no longer exists")

    input ("Press any key to continue")

    # disconnect once again
    print ("Disconnecting")
    zk.stop ()
    print ("client current state = {}".format (zk.state))

    # cleanup
    print ("Cleaning up")
    zk.close ()
    print ("client current state = {}".format (zk.state))
    
except:
        print ("Exception thrown: ", sys.exc_info()[0])

