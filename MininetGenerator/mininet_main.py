#!/usr/bin/python

#
# Vanderbilt University, Computer Science
# CS6381: Distributed Systems Principles
# Author: Aniruddha Gokhale
# Created: February 2018
# 
# Purpose:
#
# Mininet topology generator for pub-sub assignments
#

import os              # OS level utilities
import sys             # system level utilities
import random          # random number generator
import argparse        # for command line parsing

from signal import SIGINT
from time import time

# This is our topology class created specially for Mininet
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.node import CPULimitedHost
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.net import CLI
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel, info

from topology_gen import PubSub_Topo

##################################
# Command line parsing
##################################
def parseCmdLineArgs ():
    # parse the command line
    parser = argparse.ArgumentParser ()

    # add optional arguments. Each has its default.
    #
    # first all the network topology related params
    parser.add_argument ("-n", "--numNetworks", type=int, default=1, help="Number of independent autonomous networks each projecting one router")
    parser.add_argument ("-l", "--numLANs", type=int, default=1, help="Number of independent LANs per network, default 1")
    parser.add_argument ("-r", "--numSwitches", type=int, default=1, help="Number of switches in a linear topology LAN, default 1")
    parser.add_argument ("-d", "--depth", type=int, default=1, help="Tree depth, default 1 (which makes it linear else a tree)")
    parser.add_argument ("-f", "--fanout", type=int, default=2, help="Fanout per switch, default 2")
    parser.add_argument ("-c", "--controller", help="Presence of -c implies Remote (POX) else default controller is chosen", action="store_true")

    # now the pub/sub related params
    parser.add_argument ("-b", "--brokerIP", default="10.0.0.1", help="Broker's IP address, default 10.0.0.1")
    parser.add_argument ("-p", "--numPubs", type=int, default=1, help="Number of publishers (producers), default 1")
    parser.add_argument ("-s", "--numSubs", type=int, default=1, help="Number of subscribers (consumers), default 1")

    # add positional arguments in that order
    parser.add_argument ("pubdata", help="CSV file indicating publisher characteristics")
    parser.add_argument ("subdata", help="CSV file indicating subscriber characteristics")

    # parse the args
    args = parser.parse_args ()

    return args
    
#################################################
#  Generate the commands file to be sources
#
#################################################
#
# Note that at this time, we are not using this function. The goal
# will be to generate a file that places publishers and subscribers
# on the hosts of the topology
def genCommandsFile (hosts, args):
    try:
        # first remove any existing out files
        for i in range (len (hosts)):
            # check if the output file exists
            if (os.path.isfile (hosts[i].name+".out")):
                os.remove (hosts[i].name+".out")

        # create the commands file. It will overwrite any previous file with the
        # same name.
        cmds = open ("commands.txt", "w")

        # @NOTE@: for now I have commented the following line so we will have to
        # start the master manually on host h1s1

        # first create the command for the master
        #cmd_str = hosts[0].name + " python mr_wordcount.py -p " + str (args.masterport) + " -m " + str (args.map) + " -r " + str (args.reduce) + " " + args.datafile + " &> " + hosts[0].name + ".out &\n"
        #cmds.write (cmd_str)

        #  next create the command for the map workers
        for i in range (args.map):
            cmd_str = hosts[i+1].name + " python mr_mapworker.py " + str (i) + " " + hosts[0].IP () + " " + str (args.masterport) + " &> " + hosts[i+1].name + ".out &\n"
            cmds.write (cmd_str)

        #  next create the command for the reduce workers
        k = 1 + args.map   # starting index for reducer hosts (master + maps)
        for i in range (args.reduce):
            cmd_str = hosts[k+i].name + " python mr_reduceworker.py " + str (i) + " " + hosts[0].IP () + " " + str (args.masterport) + " &> " + hosts[k+i].name + ".out &\n"
            cmds.write (cmd_str)

        # close the commands file.
        cmds.close ()
        
    except:
            print "Unexpected error in run mininet:", sys.exc_info()[0]
            raise

############################################
# set per LAN IP address for each router
############################################
def setPerLANRouterIPAddr (net, topo):
    # set the IP addresses on each interface of the router that
    # connects to its local LANs
    for i in range (topo.numNetworks):
        # construct the router ID so we can retrieve the node
        # from the network object
        rID = "r"+str(i+1)
        router = net.get (rID)

        # For each LAN, set an IP address for this
        # router on that interface. The router always
        # gets the *.1/24 IP address
        for j in range (topo.numLANs):
            # retrieve the jth subnet and make that the
            # interface
            ipaddr = topo.subnets[rID][j] + str (".1/24")
            intf = rID + "-eth" + str (j+1)
            router.setIP (ip=ipaddr, intf=intf)
    
    
############################
# interconnect routers 
############################
def interconnectRouters (net, topo):
    """ interconnect routers thru a switch """

    # we also create a special subnet for routers
    # We are going to create randomly generated subnet masks
    byte1 = random.randint (100, 250)
    byte2 = random.randint (100, 250)
    byte3 = 1

    # we now create a subnet for the graph of routers
    subnet_mask = str (byte1) + "." + \
                  str (byte2) + "." + \
                  str (byte3)

    # assign an IP addr for each router on the interface
    # connecting the routers to the switch
    for i in range (topo.numNetworks):
        rID = "r"+str (i+1)
        # next available interface number is 1 more than
        # the total number of interfaces we have used
        # on this router to connect to its LANs
        intf = rID + "-eth" + str (topo.numLANs+1)
        ipaddr = subnet_mask + "." + str (i+1) + "/24"
        router = net.get (rID)
        print ("Setting router {}'s IP addr to {} on intf {}".format (rID, ipaddr, intf))
        router.setIP (ip=ipaddr, intf=intf)

    # generate a file for us to source which sets routes on the
    # routers
    f = open ("routes.sh", "w")

    # since Python uses zero-based indexing but our
    # router, switch, etc numbering goes from 1 onward, we
    # are adding +1 to the loop variables below.
    for i in range (topo.numNetworks):
        rID = "r"+str (i+1)
        router = net.get (rID)
        for j in range (topo.numNetworks):
            neighborID = "r"+str (j+1)
            neighbor = net.get (neighborID)
            
            # do only for distinct router pairs
            if i != j:
                # take the first two parts of the subnets
                # because for anything in that direction,
                # send packets to that neighbor. For that
                # we also need to get the interface so we
                # can get that router's IP addr
                s = topo.subnets[neighborID][0].split(".")
                subnet = s[0] + "." + s[1] + ".0.0"
                intf = neighborID + "-eth" + str (topo.numLANs+1)
                ipaddr = neighbor.IP (intf=intf)
                command = rID + " route add -net " + subnet + " netmask 255.255.0.0 gw " + ipaddr + " dev " + rID + "-eth" + str (topo.numLANs+1) + "\n"
                print ("Generating command: {}".format (command))
                f.write (command)

        # now add a line to print the updated routing table
        # for this router
        command = rID + " route\n"
        f.write (command)
        
    # close the file
    f.close ()

######################
# main program
######################
def main ():
    "Create the Mininet topology for the pub/sub assignment"

    # parse the command line
    parsed_args = parseCmdLineArgs ()
    
    # instantiate our topology
    print "Instantiate and build the topology"
    topo = PubSub_Topo (parsed_args)

    # create the network
    print "Instantiate network"
    if parsed_args.controller:
        print ("Instantiating mininet with remote controller")
        net = Mininet (topo=topo, link=TCLink, autoSetMacs=True, controller=RemoteController)
    else:
        print ("Instantiating mininet with default controller")
        net = Mininet (topo=topo, link=TCLink, autoSetMacs=True)

    # activate the network
    print "Activate network"
    net.start ()

    # set per LAN router IP addr
    setPerLANRouterIPAddr (net, topo)

    # interconnect the routers
    interconnectRouters (net, topo)
    
    # dump routing tables of the routers
    for i in range (topo.numNetworks):
        info( '*** Routing Table on Router:\n' )
        info( net[ 'r'+str(i+1) ].cmd( 'route' ) )

    print "Generating commands file to be sourced"
    #genCommandsFile (net.hosts, parsed_args)

    # run the cli
    CLI (net)

    # cleanup
    net.stop ()

# -----------------------------------------------------------
if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel ('info')
    main ()
