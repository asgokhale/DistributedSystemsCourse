Course: CS6381 Distributed Systems Principles
Instructor: Aniruddha Gokhale
Created: Spring 2023

Purpose:
------------

The goal of providing this starter code is to help students get started with the
programming assignment. By no means is this the best or ideal way of doing
things nor is it probably the best way to use modern Python capabilities.  I am
using my traditional C++ OO mindset and constructing the Python code in that
manner. But, we had to start somewhere and also try to have some uniformity
among the code structure of the students so that it is easier to build tests
and other scripts that are reusable and possibly shared across the class.  Hence,
this attempt.

Directory Structure:
---------------------------

PublisherAppln.py:
        Provides the starter code for the publisher application-level capabilities.
        Recall that we are planning to approach the ideal goals of decoupling
        at time, space and synchronization levels. We achieve this at the
        application-level but then this breaks at the lower level which is
        our middleware. Read the description and the purpose inside the
        PubAppln.py file to see how it is supposed to operate. Make needed
        modifications.

SubscriberAppln.py:
        Provides the starter code for the subscriber application-level capabilities.
        Recall that we are planning to approach the ideal goals of decoupling
        at time, space and synchronization levels. We achieve this at the
        application-level but then this breaks at the lower level which is
        our middleware. Read the description and the purpose inside the
        SubAppln.py file to see how it is supposed to operate. Make needed
        modifications.

DiscoveryAppln.py:
        Provides the starter code for the centralized Discovery service, which is
        the focus of Assignment 1. All entities in the system must register with
        the discovery service letting it know what role do they play, topics
        of interest, their whereabouts, etc. Few more operations are supported
        on the Discovery service, such as lookup, ready, etc. All of these will
        use the ProtoBufs to send/receive serialized information.  For that, we
        must define the appropriate schema in the *.proto file and run it
        through the protoc compiler to generate the underlying code needed
        to serialize/deserialize the data.

BrokerAppln.py:
        Provides the starter code for the broker application-level capabilities.
        Recall that one of the dissemination strategies is via the broker. It is
        only in that case that this broker application will be actively used.
        When this strategy is active, then all dissemination must happen via
        the broker. So all publishers send their publications to the broker.
        In other words, the broker serves as a proxy on behalf of all the
        subscribers and thus becomes the one single subscriber to every
        publisher. It wil receive all publications from all publishers. But now,
        it must determine which publications actually go to which subscribers.
        The broker becomes a publisher proxy to all subscribers.

CS6381_MW:  (Note this is a folder)
        This is the directory under which we will hide all the networking details
        including the use of ZMQ and its different socket types that are needed
        for the client-server and pub-sub capabilities. All the decoupling we
        discussed breaks at this layer but that is alright as somewhere it needs
        to break anyway. This middleware is further divided into the following files.
        Please enhance and/or add anything that might be missing.

        PublisherMW.py:
                Middleware-level publisher functionality. It will maintain the ZMQ PUB
                socket needed for publication while use ZMQ REQ socket for talking
                to the Discovery service.
                
        SubscriberMW.py:
                Middleware-level subscriber functionality. It will maintain the ZMQ SUB
                socket needed for subscription while use ZMQ REQ socket for talking
                to the Discovery service.
                
        DiscoveryMW.py:
                Middleware-level centralized lookup functionality. It will maintain the
                ZMQ REP socket needed for responding to all client requests. Enhance
                the capabilities as needed.
                
        BrokerMW.py:
                Middleware-level broker functionality. It will maintain both the ZMQ PUB
                and ZMQ SUB sockets needed for publication/subscription on behalf of the
                publishers and subscribers, respectively. It will use ZMQ REQ socket for talking
                to the Discovery service.

        discovery.proto:
                Message formats for accessing the services of the Discovery services. Several
                of these must be modified by the students.

        discovery_pb2.py:
                File generated by running the protoc compiler on the discovery.proto file. Here
                we invoked the following command:

                           protoc --python_out="./" discovery.proto


                
        
