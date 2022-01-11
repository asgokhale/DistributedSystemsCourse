#  Author: Aniruddha Gokhale
#  Created: Fall 2019
#  Modified: Spring 2021 to cater to API changes and comment the code
#
#  Purpose: demonstrate serialization of topic data type using flatbuffers
#
#  Here our topic comprises a sequence number, a timestamp, and a data buffer
#  of several uint32 numbers (whose value is not relevant to us)

import os
import sys

# this is needed to tell python where to find the flatbuffers package
# make sure to change this path to where you have installed flatbuffers
sys.path.append(os.path.join(os.path.dirname(__file__), '/home/gokhale/Apps/flatbuffers/python'))
import flatbuffers    # this is the flatbuffers package we import
import time   # we need this get current time
import numpy as np
import MyPubSub.Topic as mt   # this is the generated code by the flatbuffer compiler

# This is the method we will use in our main program
def serialize (seq_num, name, vec_len):
    # get the builder object
    builder = flatbuffers.Builder (0);

    # create the name string that we will use
    name_field = builder.CreateString (name)
    
    # create the array that we will add to our buffer
    mt.StartDataVector (builder, vec_len)
    for i in reversed (range (vec_len)):
        builder.PrependUint32 (i)
    data = builder.EndVector ()
    
    # let us create a topic and add contents to it.
    # Our topic consists of a seq num, timestamp, and an array of longs
    mt.Start (builder)
    mt.AddSeqNo (builder, seq_num)
    mt.AddTs (builder, time.time ())
    mt.AddName (builder, name_field)
    mt.AddData (builder, data)
    topic = mt.End (builder)

    # end the serialization process
    builder.Finish (topic)

    # get the serialized buffer
    buf = builder.Output ()

    return buf

# deserialize the incoming serialized structure into native data type
def deserialize (buf):
    recvd_topic = mt.Topic.GetRootAs (buf, 0)

    # sequence number
    print ("Sequence num = {}".format (recvd_topic.SeqNo ()))

    # topic name received
    print ("received name = {}".format (recvd_topic.Name ()))

    # received vector data
    print ("Received vector has {} elements".format (recvd_topic.DataLength ()))
    print ("Received vector as numpy {}".format (recvd_topic.DataAsNumpy ()))
    
    # latency = current timestamp minus incoming timestamp
    latency = time.time () - recvd_topic.Ts ()
    print ("Latency for receiving = {}".format (latency))

    if (recvd_topic.Name () == b'END'):
        return 0
    else:
        return 1
    

if __name__ == '__main__':
    main()
