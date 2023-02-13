
import os
import sys
from uhashring import HashRing

nodes = {
  'node1' : {
    'hostname': '10.0.0.1',
    'instance': None,
    'port': 5555,
    'vnodes': 1,
    'weight': 1
  },
  'node2' : {
    'hostname': '10.0.0.2',
    'instance': None,
    'port': 5555,
    'vnodes': 1,
    'weight': 1
  },
  'node3' : {
    'hostname': '10.0.0.3',
    'instance': None,
    'port': 5555,
    'vnodes': 1,
    'weight': 1
  },
  'node4' : {
    'hostname': '10.0.0.4',
    'instance': None,
    'port': 5555,
    'vnodes': 1,
    'weight': 1
  },
  'node5' : {
    'hostname': '10.0.0.5',
    'instance': None,
    'port': 5555,
    'vnodes': 1,
    'weight': 1
  },
  'node6' : {
    'hostname': '10.0.0.6',
    'instance': None,
    'port': 5555,
    'vnodes': 1,
    'weight': 1
  },
  'node7' : {
    'hostname': '10.0.0.7',
    'instance': None,
    'port': 5555,
    'vnodes': 1,
    'weight': 1
  },
  'node8' : {
    'hostname': '10.0.0.8',
    'instance': None,
    'port': 5555,
    'vnodes': 1,
    'weight': 1
  },
  'node9' : {
    'hostname': '10.0.0.9',
    'instance': None,
    'port': 5555,
    'vnodes': 1,
    'weight': 1
  },
  'node10' : {
    'hostname': '10.0.0.10',
    'instance': None,
    'port': 5555,
    'vnodes': 1,
    'weight': 1
  }
}

hr = HashRing (nodes)

print (hr)
print ("Nodes: {}".format (hr.nodes))
print ("Ring size: {}".format (hr.size))
print ("Distribution: {}".format (hr.distribution))
#print ("Ring: {}".format (hr.ring))
