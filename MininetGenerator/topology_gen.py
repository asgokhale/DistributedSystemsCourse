#!/usr/bin/python

#
# Vanderbilt University, Computer Science
# CS6381: Distributed Systems Principles
# Author: Aniruddha Gokhale
# Created: February 2018
# 
# Purpose:
#
# Topology class for generating topologies for the
# pub/sub assignment
#

import os              # OS level utilities
import sys             # system level utilities
import random          # random number generator

# These are all Mininet-specific
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import pmonitor, irange, natural, naturalSeq
from mininet.log import setLogLevel, info

#---------------------------------------------------------------------
# This class is taken as is from the Mininet examples directory which
# serves as a router to connect the independent LANs in our topology
class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."

    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()

#---------------------------------------------------------------------
# This class will define the derived topology class for the pub/sub
# assignment.  Over time it is my desire to make this more generic
#
# For now we enable the creation of multiple LANs. Each LAN may have its
# own tree or linear topologies. The root-level switches of each LAN are
# then connected in some fashion, e.g., linear or some complex graph.
# But that will need some more thinking and so for now we just use linear
#
class PubSub_Topo (Topo):
    "Topology class for the pub/sub assignment."

    # ------------------------------------------------------------------
    # "build" method that is automatically invoked by the topology
    # generation logic of Mininet
    #
    def build (self, args, **_opts):
        """Famous build method"""

        # network topology related params
        self.numNetworks = args.numNetworks # number of distinct autonomous networks
        self.numLANs = args.numLANs    # number of independent LANs per network
        self.numSwitches = args.numSwitches # number of switches for linear topo
        self.depth = args.depth        # depth per root switch of each LAN
        self.fanout = args.fanout      # fanout at each depth

        # pub/sub related params
        self.brokerIP = args.brokerIP  # IP address where broker is to be placed
        self.numPubs = args.numPubs    # number of publishers
        self.numSubs = args.numSubs    # number of subscribers
        self.pubdata = args.pubdata    # supplies properties of publishers
        self.subdata = args.subdata    # supplies properties of subscribers

        self.routers = []         # All the routers
        self.subnets = {}         # generated subnets indexed by its router
        self.lanGateways = {}     # gateway switch per LAN for each independent network

        # dump details
        self.dump ()
        
        # Build the network topology
        self.build_complete_network ()


    # ------------------------------------------------------------------
    # debug
    #
    def dump (self):
        print ("\n=======================================================")
        print ("Broker IP = {}".format (self.brokerIP))
        print ("Number of Networks = {}".format (self.numNetworks))
        print ("Number of LANs = {}".format (self.numLANs))
        print ("Switches per LAN = {}".format (self.numSwitches))
        print ("Num of hosts per switch = {}".format (self.fanout))
        print ("Tree depth = {}".format (self.depth))
        print ("=======================================================\n")
        
    # ------------------------------------------------------------------
    # This starts the network building process
    #
    def build_complete_network (self):
        """Builds the complete network topology"""
        print ("Building network topology")

        for i in range (self.numNetworks):
            # build each network. We number them from 1 onward
            self.build_network (i+1)

        # now build a network of routers by connecting them via a switch
        coreSW = self.addSwitch ("s0")
        for i in range (self.numNetworks):
            intf = self.routers[i] + "-eth" + str (self.numLANs+1)
            self.addLink (self.routers[i], coreSW, intfName1=intf)
                    
        
            
    # ------------------------------------------------------------------
    # Builds each individual network
    #
    def build_network (self, id):

        # The router will get an id like r0, r1, r2 ... depending on
        # the id parameter
        rID = "r" + str(id)
        self.subnets[rID] = []
        
        # We are going to create randomly generated subnet masks
        # for the different LANs we are going to have. All subnets
        # are assumed to be of the form a.b.c.x/24. Only the 3rd byte
        # gets incremented by 1 for each individual LAN of the given n/w.
        byte1 = random.randint (100, 250)
        byte2 = random.randint (100, 250)
        byte3 = 1
        for i in range (self.numLANs):
            subnet_mask = str (byte1) + "." + \
                          str (byte2) + "." + \
                          str (byte3+i)
            self.subnets[rID].append (subnet_mask)
            
        # add a single core router to interconnect all LAN switches
        # of this autonomous network
        #
        router = self.addNode( rID, cls=LinuxRouter, ip=self.subnets[rID][0]+".1/24")
        self.routers.append (router)

        # now build the individual LANs within this autonomous network
        self.build_lans (router)

        # connect this router to all the gateway switches
        # in each LAN 
        for i in irange (1, self.numLANs):
            routerIP = self.subnets[router][i-1] + ".1/24"
            intf = router +'-eth' + str (i)
            print ("Adding link between {} and router {} with interface {} and router IP {}".format (self.lanGateways[router][i-1], router, intf, routerIP))
            self.addLink (self.lanGateways[router][i-1], router, intfName2=intf, params2 ={ 'ip' : routerIP } ) 
        
    # ------------------------------------------------------------------
    # This builds the individual LANs
    #
    # Unless we upgrade this code to actually use user-defined
    # subnet and subnet masks, we are going to assume that the
    # LANs are going to be of the form a.b.c.x/24
    # The router will always have the *.1 address on its interface
    # while hosts will start their numbering from *.100
    #
    def build_lans (self, router):
        """Builds individual LANs"""
        print ("Number of LANs to be built for n/w# {}: {}".format (router, self.numLANs))
        # create an empty entry to store the gateway switches for all
        # the LANs for this network
        self.lanGateways[router] = []

        # build each LAN and retrieve its gateway switch
        for i in irange (1, self.numLANs):
            # now check if the depth is 1 or more. If 1, then it is a
            # linear topology else it is a tree topology
            if (self.depth == 1):
                # We use LAN number to build both our subnet as well
                # as naming convention for LANs/switches/hosts
                gatewaySwitch = self.build_linear_topo (router, i)
            elif (self.depth > 1):
                print ("Depth > 1")
            else:
                print ("Depth must be >= 1");
                return

            # save the gateway switch
            self.lanGateways[router].append (gatewaySwitch)
                

    # ------------------------------------------------------------------
    # This builds a linear topology using name prefixes
    #
    # We had to do this because we want to create multiple
    # networks and the Mininet-supplied function always creates
    # host and switch names that are h1, h2 ... and s1, s2, ...
    #
    # The logic is actually exactly the same from the Mininet
    # source code.
    #
    def build_linear_topo (self, router, lanID):
        """lanID: LAN id """

        # define a lambda function for naming a host
        # which is going to be the LAN number followed by
        # switch number followed by host number.
        name_prefix = router + "l" + str (lanID)  

        # Lambda functions: for host, i is switch prefix, j is host prefix.
        genHostName = lambda i, j: name_prefix+'s%dh%s' % ( i, j )
        genSwitchName = lambda i: name_prefix+'s%s' % ( i )

        # We keep track of the last switch and use it as the
        # gateway switch of this LAN
        lastSwitch = None
        k = 0
        for i in irange( 1, self.numSwitches ):
            # First add a switch; 
            switch = self.addSwitch( genSwitchName (i) ) 

            # Next, add hosts to that switch and set a link from
            # the host to the switch
            for j in irange( 1, self.fanout ):
                # We also add its IP address and default route
                # IP addresses start at *.101 ...
                ipaddr = self.subnets[router][lanID-1] + str (".") + str (100+k) + "/24"
                route = "via " + self.subnets[router][lanID-1] + ".1"
                #print ("Currently handling host: {} with IP addr: {} and route: {}".format (genHostName (i, j), ipaddr, route))
                host = self.addHost( genHostName( i, j ), ip=ipaddr, defaultRoute=route )
                # add a link between this host and its parent switch
                #print ("Adding link between host: {} and switch: {}".format (genHostName (i,j), genSwitchName (i)))
                self.addLink( host, switch )
                k = k + 1

            # Connect switch to previous
            if lastSwitch:
                self.addLink( switch, lastSwitch )

            # remember the last added switch
            lastSwitch = switch        

        # Whoever is the very last switch in this LAN gets connected
        # to the router.
        #
        # return that final switch that we added
        return lastSwitch
