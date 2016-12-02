'''
Created on Oct 12, 2016
@author: mwitt_000
'''
import network_1
import link_1
import threading
from time import sleep
import sys

##configuration parameters
router_queue_size = 0 #0 means unlimited
simulation_time = 10 #give the network sufficient time to transfer all packets before quitting

if __name__ == '__main__':
    object_L = [] #keeps track of objects, so we can kill their threads
    
    #create network hosts
    client = network_1.Host(1)
    object_L.append(client)
    server = network_1.Host(2)
    object_L.append(server)
    
    #create routers and routing tables for connected clients (subnets)
    router_a_rt_tbl_D = {1: {0: 1}} # packet to host 1 through interface 0 for cost 1
    router_a = network_1.Router(name='A', 
                              intf_cost_L=[1,1], 
                              intf_capacity_L=[500,500],
                              rt_tbl_D = router_a_rt_tbl_D, 
                              max_queue_size=router_queue_size)
    object_L.append(router_a)
    router_b_rt_tbl_D = {2: {1: 3}} # packet to host 2 through interface 1 for cost 3
    router_b = network_1.Router(name='B', 
                              intf_cost_L=[1,3], 
                              intf_capacity_L=[500,100],
                              rt_tbl_D = router_b_rt_tbl_D, 
                              max_queue_size=router_queue_size)
    object_L.append(router_b)
    
    #create a Link Layer to keep track of links between network nodes
    link_layer = link_1.LinkLayer()
    object_L.append(link_layer)
    
    #add all the links
    link_layer.add_link(link_1.Link(client, 0, router_a, 0))
    link_layer.add_link(link_1.Link(router_a, 1, router_b, 0))
    link_layer.add_link(link_1.Link(router_b, 1, server, 0))
    
    
    #start all the objects
    thread_L = []
    for obj in object_L:
        thread_L.append(threading.Thread(name=obj.__str__(), target=obj.run)) 
    
    for t in thread_L:
        t.start()
    
    #create some send events    
    for i in range(5):
        priority = i%2
        print(priority)
        client.udt_send(2, 'Sample client data %d' % i, priority)
        
    #give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)
    
    #print the final routing tables
    for obj in object_L:
        if str(type(obj)) == "<class 'network.Router'>":
            obj.print_routes()
    
    #join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()
        
    print("All simulation threads joined")



# writes to host periodically