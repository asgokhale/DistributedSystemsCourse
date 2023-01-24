###############################################
#
# Author: Aniruddha Gokhale
# Vanderbilt University
#
# Purpose: Skeleton/Starter code for the publisher middleware code
#
# Created: Spring 2023
#
###############################################

# The publisher middleware does not do anything on its own. It must be used
# by the application level logic. This middleware object maintains the ZMQ
# sockets and knows how to talk to Discovery service, etc.
#
# Here is what this middleware should do
# (1) it must maintain the ZMQ sockets, one in the REQ role to talk to the Discovery service
# and one in the PUB role to disseminate topics
# (2) It must, on behalf of the application logic, register the publisher application with the
# discovery service. To that end, it must use the protobuf-generated serialization code to
# send the appropriate message with the contents to the discovery service.
# (3) On behalf of the publisher appln, it must also query the discovery service (when instructed) 
# to see if it is fine to start dissemination
# (4) It must do the actual dissemination activity of the topic data when instructed by the 

# import the needed packages
import os     # for OS functions
import sys    # for syspath and system exception
import time   # for sleep
import argparse # for argument parsing
import configparser # for configuration parsing
import logging # for logging. Use it in place of print statements.
import zmq  # ZMQ sockets

# import serialization logic
from CS6381_MW import discovery_pb2

# import any other packages you need.

##################################
#       Publisher Middleware class
##################################
class PublisherMW ():

  ########################################
  # constructor
  ########################################
  def __init__ (self, logger):
    self.logger = logger  # internal logger for print statements
    self.pub = None # will be a ZMQ PUB socket for dissemination
    self.req = None # will be a ZMQ REQ socket to talk to Discovery service
    self.poller = None # used to wait on incoming replies
    self.addr = None # our advertised IP address
    self.port = None # port num where we are going to publish our topics

  ########################################
  # configure/initialize
  ########################################
  def configure (self, args):
    ''' Initialize the object '''

    try:
      # Here we initialize any internal variables
      self.logger.debug ("PublisherMW::configure")

      # First retrieve our advertised IP addr and the publication port num
      self.port = args.port
      self.addr = args.addr
      
      # Next get the ZMQ context
      self.logger.debug ("PublisherMW::configure - obtain ZMQ context")
      context = zmq.Context ()  # returns a singleton object

      # get the ZMQ poller object
      self.logger.debug ("PublisherMW::configure - obtain the poller")
      self.poller = zmq.Poller ()
      
      # Now acquire the REQ and PUB sockets
      self.logger.debug ("PublisherMW::configure - obtain REQ and PUB sockets")
      self.req = context.socket (zmq.REQ)
      self.pub = context.socket (zmq.PUB)

      # register the REQ socket for incoming events
      self.logger.debug ("PublisherMW::configure - register the REQ socket for incoming replies")
      self.poller.register (self.req, zmq.POLLIN)
      
      # Now connect ourselves to the discovery service. Recall that the IP/port were
      # supplied in our argument parsing.
      self.logger.debug ("PublisherMW::configure - connect to Discovery service")
      # For these assignments we use TCP. The connect string is made up of
      # tcp:// followed by IP addr:port number.
      connect_str = "tcp://" + args.discovery
      self.req.connect (connect_str)
      
      # Since we are the publisher, the best practice as suggested in ZMQ is for us to
      # "bind" to the PUB socket
      self.logger.debug ("PublisherMW::configure - bind to the pub socket")
      # note that we publish on any interface hence the * followed by port number.
      # We always use TCP as the transport mechanism (at least for these assignments)
      bind_string = "tcp://*:" + self.port
      self.pub.bind (bind_string)
      
    except Exception as e:
      raise e

  ########################################
  # register with the discovery service
  ########################################
  def register (self, name, topiclist):
    ''' register the appln with the discovery service '''

    try:
      self.logger.debug ("PublisherMW::register")

      # as part of registration with the discovery service, we send
      # what role we are playing, the list of topics we are publishing,
      # and our whereabouts, e.g., name, IP and port

      # TO-DO
      # Recall that the current defns of the messages in discovery.proto file
      # are treating everything as string. But you are required to change those.
      # So in this code, I am showing the serialization based on existing defns.
      # This will change once you make changes in the proto file.

      # The following code shows serialization using the protobuf generated code.
      
      # first build a register req message
      self.logger.debug ("PublisherMW::register - populate the nested register req")
      register_req = discovery_pb2.RegisterReq ()  # allocate 
      register_req.role = "publisher"  # this will change to an enum later on
      comma_sep_topics = ','.join (topiclist) # converts list into comma sep string
      register_req.topiclist = comma_sep_topics   # fill up the topic list
      unique_id = name + ":" + self.addr + ":" + self.port
      register_req.id = unique_id  # fill up the ID
      self.logger.debug ("PublisherMW::register - done populating nested RegisterReq")

      # Build the outer layer Discovery Message
      self.logger.debug ("PublisherMW::register - build the outer DiscoveryReq message")
      disc_req = discovery_pb2.DiscoveryReq ()
      disc_req.msg_type = discovery_pb2.REGISTER
      # It was observed that we cannot directly assign the nested field here.
      # A way around is to use the CopyFrom method as shown
      disc_req.register_req.CopyFrom (register_req)
      self.logger.debug ("PublisherMW::register - done building the outer message")
      
      # now let us stringify the buffer and print it. This is actually a sequence of bytes and not
      # a real string
      buf2send = disc_req.SerializeToString ()
      self.logger.debug ("Stringified serialized buf = {}".format (buf2send))

      # now send this to our discovery service
      self.logger.debug ("PublisherMW::register - send stringified buffer to Discovery service")
      self.req.send (buf2send)  # we use the "send" method of ZMQ that sends the bytes

      # now go to our event loop to receive a response to this request
      self.logger.debug ("PublisherMW::register - now wait for reply")
      return self.event_loop ()
      
    
    except Exception as e:
      raise e

  ########################################
  # check if the discovery service gives us a green signal to proceed
  ########################################
  def is_ready (self):
    ''' register the appln with the discovery service '''

    try:
      self.logger.debug ("PublisherMW::is_ready")

      # we do a similar kind of serialization as we did in the register
      # message but much simpler, and then send the request to
      # the discovery service
    
      # The following code shows serialization using the protobuf generated code.
      
      # first build a IsReady message
      self.logger.debug ("PublisherMW::is_ready - populate the nested IsReady msg")
      isready_msg = discovery_pb2.IsReadyReq ()  # allocate 
      # actually, there is nothing inside that msg declaration.
      self.logger.debug ("PublisherMW::is_ready - done populating nested IsReady msg")

      # Build the outer layer Discovery Message
      self.logger.debug ("PublisherMW::is_ready - build the outer DiscoveryReq message")
      disc_req = discovery_pb2.DiscoveryReq ()
      disc_req.msg_type = discovery_pb2.ISREADY
      # It was observed that we cannot directly assign the nested field here.
      # A way around is to use the CopyFrom method as shown
      disc_req.is_ready.CopyFrom (isready_msg)
      self.logger.debug ("PublisherMW::is_ready - done building the outer message")
      
      # now let us stringify the buffer and print it. This is actually a sequence of bytes and not
      # a real string
      buf2send = disc_req.SerializeToString ()
      self.logger.debug ("Stringified serialized buf = {}".format (buf2send))

      # now send this to our discovery service
      self.logger.debug ("PublisherMW::is_ready - send stringified buffer to Discovery service")
      self.req.send (buf2send)  # we use the "send" method of ZMQ that sends the bytes
      
      # now go to our event loop to receive a response to this request
      self.logger.debug ("PublisherMW::is_ready - now wait for reply")
      return self.event_loop ()
      
    except Exception as e:
      raise e

  #################################################################
  # run the event loop where we expect to receive a reply to a sent request
  #################################################################
  def event_loop (self):

    try:
      self.logger.debug ("PublisherMW::event_loop - run the event loop")

      while True:
        # poll for events. We give it an infinite timeout.
        # The return value is a socket to event mask mapping
        events = dict (self.poller.poll ())
      
        # the only socket that should be enabled, if at all, is our REQ socket.
        if self.req in events:  # this is the only socket on which we should be receiving replies
          # handle the incoming reply and return the result
          return self.handle_reply ()

    except Exception as e:
      raise e
            
  #################################################################
  # handle an incoming reply
  #################################################################
  def handle_reply (self):

    try:
      self.logger.debug ("PublisherMW::handle_reply")

      # let us first receive all the bytes
      bytesRcvd = self.req.recv ()

      # now use protobuf to deserialize the bytes
      disc_resp = discovery_pb2.DiscoveryResp ()
      disc_resp.ParseFromString (bytesRcvd)

      # depending on the message type, the remaining
      # contents of the msg will differ

      # TO-DO
      # When your proto file is modified, some of this here
      # will get modified.
      if (disc_resp.msg_type == discovery_pb2.REGISTER):
        # this is a response to register message
        return disc_resp.register_resp.result
      elif (disc_resp.msg_type == discovery_pb2.ISREADY):
        # this is a response to is ready request
        return disc_resp.is_ready.reply
      else: # anything else is unrecognizable by this object
        # raise an exception here
        raise Exception ("Unrecognized response message")

    except Exception as e:
      raise e
            
            
  #################################################################
  # disseminate the data on our pub socket
  #################################################################
  def disseminate (self, data):
    try:
      self.logger.debug ("PublisherMW::disseminate - {}".format (data))
      self.pub.send_string (data)

    except Exception as e:
      raise e
            
