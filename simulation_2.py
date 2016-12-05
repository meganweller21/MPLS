'''
Created on Oct 12, 2016
@author: mwitt_000
'''
import network_2
import link_2
import threading
from time import sleep
import sys

##configuration parameters
router_queue_size = 0 #0 means unlimited
simulation_time = 10 #give the network sufficient time to transfer all packets before quitting

if __name__ == '__main__':
    object_L = [] #keeps track of objects, so we can kill their threads
    
    #create network hosts
    host1 = network_2.Host(1)
    object_L.append(host1)
    host2 = network_2.Host(2)
    object_L.append(host2)
    host3 = network_2.Host(3)
    object_L.append(host3)
    
    #create routers and routing tables for connected clients (subnets)

    #Labels we made:
    # A = 10
    # B = 11
    # C = 12
    # D = 13
    #format: in_label, in_intf, out_label, out_intf

    # forwarding_table = [A, 0, B, 0]     [B, 0, D, 1]   [A, 1, C, 3]    [C, 0, D, 1]
    forwarding_table = [[[10, 0, 11, 2], [11, 0, 13, 1], [10, 1, 12, 3], [12, 0, 13, 1]]]
    router_a_rt_tbl_D = {1: {0: 1}, 2: {1: 9}}
    router_a = network_2.Router(name='A', 
                              intf_cost_L=[1,9,1,2],
                              intf_capacity_L=[500,500,500,500],
                              rt_tbl_D = router_a_rt_tbl_D, 
                              max_queue_size=router_queue_size,
                              forwarding_table = forwarding_table)
    object_L.append(router_a)
    router_b_rt_tbl_D = {1: {0: 2}, 3: {1: 5}}
    router_b = network_2.Router(name='B', 
                              intf_cost_L=[1,2], 
                              intf_capacity_L=[500,100],
                              rt_tbl_D = router_b_rt_tbl_D, 
                              max_queue_size=router_queue_size,
                              forwarding_table = forwarding_table)
    object_L.append(router_b)
    router_c_rt_tbl_D = {1: {0: 3}, 3: {1: 4}}
    router_c = network_2.Router(name='C', 
                              intf_cost_L=[2,1], 
                              intf_capacity_L=[500,500], #I made this up
                              rt_tbl_D = router_c_rt_tbl_D, 
                              max_queue_size=router_queue_size,
                              forwarding_table = forwarding_table)
    object_L.append(router_c)
    router_d_rt_tbl_D = {3: {2: 3}}
    router_d = network_2.Router(name='D', 
                              intf_cost_L=[2,1,3], 
                              rt_tbl_D = router_d_rt_tbl_D, 
                              intf_capacity_L=[500,300,500], #I made this up
                              max_queue_size=router_queue_size,
                              forwarding_table = forwarding_table)
    object_L.append(router_d)
    
    #create a Link Layer to keep track of links between network nodes
    link_layer = link_2.LinkLayer()
    object_L.append(link_layer)
    
    #add all the links
    link_layer.add_link(link_2.Link(host1, 0, router_a, 0))
    link_layer.add_link(link_2.Link(host2, 0, router_a, 1))
    link_layer.add_link(link_2.Link(router_a, 2, router_b, 0))
    link_layer.add_link(link_2.Link(router_a, 3, router_c, 0))
    link_layer.add_link(link_2.Link(router_b, 1, router_d, 0))
    link_layer.add_link(link_2.Link(router_c, 1, router_d, 1))
    link_layer.add_link(link_2.Link(router_d, 2, host3, 0))
    
    #start all the objects
    thread_L = []
    for obj in object_L:
        thread_L.append(threading.Thread(name=obj.__str__(), target=obj.run)) 
    
    for t in thread_L:
        t.start()
    
    #router_b.send_routes(1)
    #router_c.send_routes(3)

    #create some send events    
    for i in range(5):
        priority = i%2
        print(priority)
        host1.udt_send(2, 'Sample host1 data %d' % i, priority)
        
    #give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)
    '''
    for i in range(5):
        priority = i%2
        print(priority)
        host2.udt_send(2, 'Sample host2 data %d' % i, priority)

    sleep(simulation_time)
    '''
    
    #print the final routing tables
    for obj in object_L:
        if str(type(obj)) == "<class 'network_2.Router'>":
            obj.print_routes()
    
    #join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()
        
    print("All simulation threads joined")



# writes to host periodically