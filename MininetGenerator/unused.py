    # set the routes for each router
    for i in range (topo.numNetworks):
        rID = "r"+str (i)
        router = net.get (rID)
        for j in range (topo.numNetworks):
            neighborID = "r"+str (j)
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
                command = "route add -net " + subnet + " netmask 255.255.0.0 gw " + ipaddr + " dev " + rID + "-eth" + str (topo.numLANs+1)
                print ("Executing command: {} on router: {}".format (command, rID))
                router.cmd (command)
                
    
