###############################################
#
# Author: Aniruddha Gokhale
# Vanderbilt University
#
# Purpose: Skeleton/Starter code for the publisher application
#
# Created: Spring 2023
#
###############################################


# The core logic of the publisher application will be as follows
# (1) The publisher app decides which all topics it is going to publish.
# For this assignment, we don't care about the values etc for these topics.
#
# (2) the application obtains a handle to the lookup/discovery service using
# the CS6381_MW middleware APIs so that it can register itself with the
# lookup service. Essentially, it simply delegates this activity to the underlying
# middleware publisher object.
#
# (3) Register with the lookup service letting it know all the topics it is publishing
# and any other details needed for the underlying middleware to make the
# communication happen via ZMQ
#
# (4) Keep periodically checking with the discovery service if the entire system is
# initialized so that the publisher knows that it can proceed with its periodic publishing.
#
# (5) Start a loop on the publisher for sending of topics
#
#       In each iteration, the appln decides (randomly) on which all
#       topics it is going to publish, and then accordingly invokes
#       the publish method of the middleware passing the topic
#       and its value. 
#
#       Note that additional info like timestamp etc may also need to
#       be sent and the whole thing serialized under the hood before
#       actually sending it out. Use Protobuf for this purpose
#
#
# (6) When the loop terminates, possibly after a certain number of
# iterations of publishing are over, proceed to clean up the objects and exit
#

# import the needed packages
import os     # for OS functions
import sys    # for syspath and system exception
import time   # for sleep
import argparse # for argument parsing
import configparser # for configuration parsing
import logging # for logging. Use it in place of print statements.

# Import our topic selector. Feel free to use alternate way to
# get your topics of interest
from topic_selector import TopicSelector

# Now import our CS6381 Middleware
from CS6381_MW.PublisherMW import PublisherMW
# We also need the message formats to handle incoming responses.
from CS6381_MW import discovery_pb2

# import any other packages you need.
from enum import Enum  # for an enumeration we are using to describe what state we are in

##################################
#       PublisherAppln class
##################################
class PublisherAppln ():

  # these are the states through which our publisher appln object goes thru.
  # We maintain the state so we know where we are in the lifecycle and then
  # take decisions accordingly
  class State (Enum):
    INITIALIZE = 0,
    CONFIGURE = 1,
    REGISTER = 2,
    ISREADY = 3,
    DISSEMINATE = 4,
    COMPLETED = 5

  ########################################
  # constructor
  ########################################
  def __init__ (self, logger):
    self.state = self.State.INITIALIZE # state that are we in
    self.name = None # our name (some unique name)
    self.topiclist = None # the different topics that we publish on
    self.iters = None   # number of iterations of publication
    self.frequency = None # rate at which dissemination takes place
    self.num_topics = None # total num of topics we publish
    self.lookup = None # one of the diff ways we do lookup
    self.dissemination = None # direct or via broker
    self.mw_obj = None # handle to the underlying Middleware object
    self.logger = logger  # internal logger for print statements

  ########################################
  # configure/initialize
  ########################################
  def configure (self, args):
    ''' Initialize the object '''

    try:
      # Here we initialize any internal variables
      self.logger.info ("PublisherAppln::configure")

      # set our current state to CONFIGURE state
      self.state = self.State.CONFIGURE
      
      # initialize our variables
      self.name = args.name # our name
      self.iters = args.iters  # num of iterations
      self.frequency = args.frequency # frequency with which topics are disseminated
      self.num_topics = args.num_topics  # total num of topics we publish

      # Now, get the configuration object
      self.logger.debug ("PublisherAppln::configure - parsing config.ini")
      config = configparser.ConfigParser ()
      config.read (args.config)
      self.lookup = config["Discovery"]["Strategy"]
      self.dissemination = config["Dissemination"]["Strategy"]
    
      # Now get our topic list of interest
      self.logger.debug ("PublisherAppln::configure - selecting our topic list")
      ts = TopicSelector ()
      self.topiclist = ts.interest (self.num_topics)  # let topic selector give us the desired num of topics

      # Now setup up our underlying middleware object to which we delegate
      # everything
      self.logger.debug ("PublisherAppln::configure - initialize the middleware object")
      self.mw_obj = PublisherMW (self.logger)
      self.mw_obj.configure (args) # pass remainder of the args to the m/w object
      
      self.logger.info ("PublisherAppln::configure - configuration complete")
      
    except Exception as e:
      raise e

  ########################################
  # driver program
  ########################################
  def driver (self):
    ''' Driver program '''

    try:
      self.logger.info ("PublisherAppln::driver")

      # dump our contents (debugging purposes)
      self.dump ()

      # First ask our middleware to keep a handle to us to make upcalls.
      # This is related to upcalls. By passing a pointer to ourselves, the
      # middleware will keep track of it and any time something must
      # be handled by the application level, invoke an upcall.
      self.logger.debug ("PublisherAppln::driver - upcall handle")
      self.mw_obj.set_upcall_handle (self)

      # the next thing we should be doing is to register with the discovery
      # service. But because we are simply delegating everything to an event loop
      # that will call us back, we will need to know when we get called back as to
      # what should be our next set of actions.  Hence, as a hint, we set our state
      # accordingly so that when we are out of the event loop, we know what
      # operation is to be performed.  In this case we should be registering with
      # the discovery service. So this is our next state.
      self.state = self.State.REGISTER

      # Now simply let the underlying middleware object enter the event loop
      # to handle events. However, a trick we play here is that we provide a timeout
      # of zero so that control is immediately sent back to us where we can then
      # register with the discovery service and then pass control back to the event loop
      #
      # As a rule, whenever we expect a reply from remote entity, we set timeout to
      # None or some large value, but if we want to send a request ourselves right away,
      # we set timeout is zero.
      #
      self.mw_obj.event_loop (timeout=0)  # start the event loop
      
      self.logger.info ("PublisherAppln::driver completed")
      
    except Exception as e:
      raise e

  ########################################
  # generic invoke method called as part of upcall
  #
  # This method will get invoked as part of the upcall made
  # by the middleware's event loop after it sees a timeout has
  # occurred.
  ########################################
  def invoke_operation (self):
    ''' Invoke operating depending on state  '''

    try:
      self.logger.info ("PublisherAppln::invoke_operation")

      # check what state are we in. If we are in REGISTER state,
      # we send register request to discovery service. If we are in
      # ISREADY state, then we keep checking with the discovery
      # service.
      if (self.state == self.State.REGISTER):
        # send a register msg to discovery service
        self.logger.debug ("PublisherAppln::invoke_operation - register with the discovery service")
        self.mw_obj.register (self.name, self.topiclist)

        # Remember that we were invoked by the event loop as part of the upcall.
        # So we are going to return back to it for its next iteration. Because
        # we have just now sent a register request, the very next thing we expect is
        # to receive a response from remote entity. So we need to set the timeout
        # for the next iteration of the event loop to a large num and so return a None.
        return None
      
      elif (self.state == self.State.ISREADY):
        # Now keep checking with the discovery service if we are ready to go
        #
        # Note that in the previous version of the code, we had a loop. But now instead
        # of an explicit loop we are going to go back and forth between the event loop
        # and the upcall until we receive the go ahead from the discovery service.
        
        self.logger.debug ("PublisherAppln::invoke_operation - check if are ready to go")
        self.mw_obj.is_ready ()  # send the is_ready? request

        # Remember that we were invoked by the event loop as part of the upcall.
        # So we are going to return back to it for its next iteration. Because
        # we have just now sent a isready request, the very next thing we expect is
        # to receive a response from remote entity. So we need to set the timeout
        # for the next iteration of the event loop to a large num and so return a None.
        return None
      
      elif (self.state == self.State.DISSEMINATE):

        # We are here because both registration and is ready is done. So the only thing
        # left for us as a publisher is dissemination, which we do it actively here.
        self.logger.debug ("PublisherAppln::invoke_operation - start Disseminating")

        # Now disseminate topics at the rate at which we have configured ourselves.
        ts = TopicSelector ()
        for i in range (self.iters):
          # I leave it to you whether you want to disseminate all the topics of interest in
          # each iteration OR some subset of it. Please modify the logic accordingly.
          # Here, we choose to disseminate on all topics that we publish.  Also, we don't care
          # about their values. But in future assignments, this can change.
          for topic in self.topiclist:
            # For now, we have chosen to send info in the form "topic name: topic value"
            # In later assignments, we should be using more complex encodings using
            # protobuf.  In fact, I am going to do this once my basic logic is working.
            dissemination_data = ts.gen_publication (topic)
            self.mw_obj.disseminate (self.name, topic, dissemination_data)

          # Now sleep for an interval of time to ensure we disseminate at the
          # frequency that was configured.
          time.sleep (1/float (self.frequency))  # ensure we get a floating point num

        self.logger.debug ("PublisherAppln::invoke_operation - Dissemination completed")

        # we are done. So we move to the completed state
        self.state = self.State.COMPLETED

        # return a timeout of zero so that the event loop sends control back to us right away.
        return 0
        
      elif (self.state == self.State.COMPLETED):

        # we are done. Time to break the event loop. So we created this special method on the
        # middleware object to kill its event loop
        self.mw_obj.disable_event_loop ()
        return None

      else:
        raise ValueError ("Undefined state of the appln object")
      
      self.logger.info ("PublisherAppln::invoke_operation completed")
    except Exception as e:
      raise e

  ########################################
  # handle register response method called as part of upcall
  #
  # As mentioned in class, the middleware object can do the reading
  # from socket and deserialization. But it does not know the semantics
  # of the message and what should be done. So it becomes the job
  # of the application. Hence this upcall is made to us.
  ########################################
  def register_response (self, reg_resp):
    ''' handle register response '''

    try:
      self.logger.info ("PublisherAppln::register_response")
      if (reg_resp.status == discovery_pb2.STATUS_SUCCESS):
        self.logger.debug ("PublisherAppln::register_response - registration is a success")

        # set our next state to isready so that we can then send the isready message right away
        self.state = self.State.ISREADY
        
        # return a timeout of zero so that the event loop in its next iteration will immediately make
        # an upcall to us
        return 0
      
      else:
        self.logger.debug ("PublisherAppln::register_response - registration is a failure with reason {}".format (response.reason))
        raise ValueError ("Publisher needs to have unique id")

    except Exception as e:
      raise e

  ########################################
  # handle isready response method called as part of upcall
  #
  # Also a part of upcall handled by application logic
  ########################################
  def isready_response (self, isready_resp):
    ''' handle isready response '''

    try:
      self.logger.info ("PublisherAppln::isready_response")

      # Notice how we get that loop effect with the sleep (10)
      # by an interaction between the event loop and these
      # upcall methods.
      if not isready_resp.status:
        # discovery service is not ready yet
        self.logger.debug ("PublisherAppln::driver - Not ready yet; check again")
        time.sleep (10)  # sleep between calls so that we don't make excessive calls

      else:
        # we got the go ahead
        # set the state to disseminate
        self.state = self.State.DISSEMINATE
        
      # return timeout of 0 so event loop calls us back in the invoke_operation
      # method, where we take action based on what state we are in.
      return 0
    
    except Exception as e:
      raise e

  ########################################
  # dump the contents of the object 
  ########################################
  def dump (self):
    ''' Pretty print '''

    try:
      self.logger.info ("**********************************")
      self.logger.info ("PublisherAppln::dump")
      self.logger.info ("------------------------------")
      self.logger.info ("     Name: {}".format (self.name))
      self.logger.info ("     Lookup: {}".format (self.lookup))
      self.logger.info ("     Dissemination: {}".format (self.dissemination))
      self.logger.info ("     Num Topics: {}".format (self.num_topics))
      self.logger.info ("     TopicList: {}".format (self.topiclist))
      self.logger.info ("     Iterations: {}".format (self.iters))
      self.logger.info ("     Frequency: {}".format (self.frequency))
      self.logger.info ("**********************************")

    except Exception as e:
      raise e

###################################
#
# Parse command line arguments
#
###################################
def parseCmdLineArgs ():
  # instantiate a ArgumentParser object
  parser = argparse.ArgumentParser (description="Publisher Application")
  
  # Now specify all the optional arguments we support
  # At a minimum, you will need a way to specify the IP and port of the lookup
  # service, the role we are playing, what dissemination approach are we
  # using, what is our endpoint (i.e., port where we are going to bind at the
  # ZMQ level)
  
  parser.add_argument ("-n", "--name", default="pub", help="Some name assigned to us. Keep it unique per publisher")

  parser.add_argument ("-a", "--addr", default="localhost", help="IP addr of this publisher to advertise (default: localhost)")

  parser.add_argument ("-p", "--port", type=int, default=5577, help="Port number on which our underlying publisher ZMQ service runs, default=5577")
    
  parser.add_argument ("-d", "--discovery", default="localhost:5555", help="IP Addr:Port combo for the discovery service, default localhost:5555")

  parser.add_argument ("-T", "--num_topics", type=int, choices=range(1,10), default=1, help="Number of topics to publish, currently restricted to max of 9")

  parser.add_argument ("-c", "--config", default="config.ini", help="configuration file (default: config.ini)")

  parser.add_argument ("-f", "--frequency", type=int,default=1, help="Rate at which topics disseminated: default once a second - use integers")

  parser.add_argument ("-i", "--iters", type=int, default=1000, help="number of publication iterations (default: 1000)")

  parser.add_argument ("-l", "--loglevel", type=int, default=logging.INFO, choices=[logging.DEBUG,logging.INFO,logging.WARNING,logging.ERROR,logging.CRITICAL], help="logging level, choices 10,20,30,40,50: default 20=logging.INFO")
  
  return parser.parse_args()


###################################
#
# Main program
#
###################################
def main ():
  try:
    # obtain a system wide logger and initialize it to debug level to begin with
    logging.info ("Main - acquire a child logger and then log messages in the child")
    logger = logging.getLogger ("PublisherAppln")
    
    # first parse the arguments
    logger.debug ("Main: parse command line arguments")
    args = parseCmdLineArgs ()

    # reset the log level to as specified
    logger.debug ("Main: resetting log level to {}".format (args.loglevel))
    logger.setLevel (args.loglevel)
    logger.debug ("Main: effective log level is {}".format (logger.getEffectiveLevel ()))

    # Obtain a publisher application
    logger.debug ("Main: obtain the publisher appln object")
    pub_app = PublisherAppln (logger)

    # configure the object
    logger.debug ("Main: configure the publisher appln object")
    pub_app.configure (args)

    # now invoke the driver program
    logger.debug ("Main: invoke the publisher appln driver")
    pub_app.driver ()

  except Exception as e:
    logger.error ("Exception caught in main - {}".format (e))
    return

    
###################################
#
# Main entry point
#
###################################
if __name__ == "__main__":

  # set underlying default logging capabilities
  logging.basicConfig (level=logging.DEBUG,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


  main ()
