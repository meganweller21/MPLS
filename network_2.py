'''
Created on Oct 12, 2016
@author: mwitt_000
'''
import queue
import threading

new_update_A = True
new_update_D = True

## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    #  @param cost - of the interface used in routing
    #  @param capacity - the capacity of the link in bps
    def __init__(self, cost=0, maxsize=0, capacity=500):
        self.in_queue = queue.PriorityQueue(maxsize);
        self.out_queue = queue.PriorityQueue(maxsize);
        self.cost = cost
        self.capacity = capacity #serialization rate
        self.next_avail_time = 0 #the next time the interface can transmit a packet
        self.p1size = 0
        self.p0size = 0
    
    ##get packet from the queue interface
    # @param in_or_out - use 'in' or 'out' interface
    def get(self, in_or_out):
        try:
            if in_or_out == 'in':
                pkt_S = self.in_queue.get(False)
                prior = pkt_S[0]
                pkt = pkt_S[1]

#                 if pkt_S is not None:
#                     print('getting packet from the IN queue')
                return (prior, pkt)
            else:
                pkt_S = self.out_queue.get(False)
                prior = pkt_S[0]
                pkt = pkt_S[1]

                if int(prior) == 0:
                    self.p0size -= 1
                else:
                    self.p1size -= 1
#                 if pkt_S is not None:
#                     print('getting packet from the OUT queue')
                return (prior, pkt)
        except queue.Empty:
            #print("I am none")
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param in_or_out - use 'in' or 'out' interface
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, priority, pkt, in_or_out, block=False):
        if in_or_out == 'out':
#             print('putting packet in the OUT queue')
            if priority == 0:
                self.p0size += 1
            else:
                self.p1size += 1

            self.out_queue.put((-priority, pkt, block))
        else:
           
#             print('putting packet in the IN queue')
            self.in_queue.put((-priority, pkt, block))
            
        
## Implements a network layer packet (different from the RDT packet 
# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
class NetworkPacket:
    ## packet encoding lengths 
    dst_addr_S_length = 5
    prot_S_length = 1
    pror_S_length = 1
    full_length = 7
    
    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    # @param prot_S: upper layer protocol for the packet (data, or control)
    def __init__(self, dst_addr, prot_S, priority, data_S):
        self.dst_addr = dst_addr
        self.data_S = data_S
        self.prot_S = prot_S
        self.priority = priority
        
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst_addr).zfill(self.dst_addr_S_length)
        if self.prot_S == 'data':
            byte_S += '1'
        elif self.prot_S == 'control':
            byte_S += '2'
        else:
            raise('%s: unknown prot_S option: %s' %(self, self.prot_S))
        byte_S += str(self.priority)
        byte_S += self.data_S
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst_addr = int(byte_S[0 : NetworkPacket.dst_addr_S_length])
        prot_S = byte_S[NetworkPacket.dst_addr_S_length : NetworkPacket.dst_addr_S_length + NetworkPacket.prot_S_length]
        if prot_S == '1':
            prot_S = 'data'
        elif prot_S == '2':
            prot_S = 'control'
        else:
            raise('%s: unknown prot_S field: %s' %(self, prot_S))
        priority_S = byte_S[NetworkPacket.dst_addr_S_length + NetworkPacket.prot_S_length : NetworkPacket.dst_addr_S_length + NetworkPacket.prot_S_length + NetworkPacket.pror_S_length]    
        data_S = byte_S[NetworkPacket.dst_addr_S_length + NetworkPacket.prot_S_length + NetworkPacket.pror_S_length : ]        
        return self(dst_addr, prot_S, priority_S, data_S)
    
class MPLS_frame(NetworkPacket):

    label_S_length = 20
    full_length = 27
    def __init__(self, label, pkt):
        self.label = label
        self.pkt = pkt
        self.prot_S = pkt.prot_S

    # called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.label).zfill(self.label_S_length)
        byte_S += self.pkt.to_byte_S()
        return byte_S

    def return_packet(self):
        return self.pkt
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        label_S = int(byte_S[0 : MPLS_frame.label_S_length])
        data_S = NetworkPacket.from_byte_S(byte_S[MPLS_frame.label_S_length : ])    
        return self(label_S, data_S)    


## Implements a network host for receiving and transmitting data
class Host:
    
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.intf_L = [Interface()]
        self.stop = False #for thread termination
    
    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)
       
    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    # @param priority: packet priority
    def udt_send(self, dst_addr, data_S, priority): #parameter used to be priority=0
        p = NetworkPacket(dst_addr, 'data', priority, data_S)
        print('%s: sending packet "%s"' % (self, p))
        self.intf_L[0].put(priority, p.to_byte_S(), 'out') #send packets always enqueued successfully
        
    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.intf_L[0].get('in')
        if pkt_S is not None:
            pkt = pkt_S[1]
            print('%s: received packet "%s"' % (self, pkt))
       
    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return
        


## Implements a multi-interface router described in class
class Router:
    
    ##@param name: friendly router name for debugging
    # @param intf_cost_L: outgoing cost of interfaces (and interface number)
    # @param intf_capacity_L: capacities of outgoing interfaces in bps 
    # @param rt_tbl_D: routing table dictionary (starting reachability), eg. {1: {1: 1}} # packet to host 1 through interface 1 for cost 1
    # @param max_queue_size: max queue length (passed to Interface)
    # @param forwarding: forwarding table for MPLS
    def __init__(self, name, intf_cost_L, intf_capacity_L, rt_tbl_D, max_queue_size, forwarding_table):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        #note the number of interfaces is set up by out_intf_cost_L
        assert(len(intf_cost_L) == len(intf_capacity_L))
        self.intf_L = []
        for i in range(len(intf_cost_L)):
            self.intf_L.append(Interface(intf_cost_L[i], max_queue_size, intf_capacity_L[i]))
        #set up the routing table for connected hosts
        self.rt_tbl_D = rt_tbl_D 
        self.forwarding_table = forwarding_table

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and 
    # process data and control packets
    def process_queues(self):
        for i in range(len(self.intf_L)):
            pkt_S = None
            #get packet from interface i
            pkt_S = self.intf_L[i].get('in')
            #if packet exists make a forwarding decision
            if pkt_S is not None:
                prior = pkt_S[0]
                pkt = pkt_S[1]
                if len(pkt) > 30:
                    p = MPLS_frame.from_byte_S(pkt)
                else:
                    p = NetworkPacket.from_byte_S(pkt) #parse a packet out
                if p.prot_S == 'data':
                    self.forward_packet(prior, p, i)
                elif p.prot_S == 'control':
                    self.update_routes(p, i)
                else:
                    raise Exception('%s: Unknown packet type in packet %s' % (self, p))
            
    ## forward the packet according to the routing table
    #  @param p Packet to forward
    #  @param i Incoming interface number for packet p
    def forward_packet(self, prior, p, i):
        try:
            # TODO: Here you will need to implement a lookup into the 
            # forwarding table to find the appropriate outgoing interface
            # for now we assume the outgoing interface is (i+1)%2
            if (len(p.to_byte_S()) > 30):
                pk = p.return_packet()
                source_host = pk.data_S[11]
            else:
                source_host = p.data_S[11]

            if (self.name == "A"):
                #coming from Host 1
                if (source_host == "1"):
                    pkt = MPLS_frame(self.forwarding_table[0][0], p)
                    interface = self.forwarding_table[0][3]
                #coming from Host 2
                elif (source_host == "2"):
                    pkt = MPLS_frame(self.forwarding_table[2][0], p)
                    interface = self.forwarding_table[2][3]
            elif (self.name == "B"):
                pkt = MPLS_frame(self.forwarding_table[1][0], p.return_packet())
                interface = self.forwarding_table[1][3]
            elif (self.name == "C"):
                pkt = MPLS_frame(self.forwarding_table[3][0], p.return_packet())
                interface = self.forwarding_table[3][3]
            elif (self.name == "D"):
                pkt = p.return_packet()
                interface = 2
              
         
            self.intf_L[interface].put(prior, pkt.to_byte_S(), 'out', True)
            print('%s: forwarding packet "%s" from interface %d to %d' % (self, pkt, i, interface))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, pkt, i))
            pass
        
    ## forward the packet according to the routing table
    #  @param p Packet containing routing information
    def update_routes(self, p, i):
        #TODO: add logic to update the routing tables and
        # possibly send out routing updates
        print('%s: Received routing update %s from interface %d' % (self, p, i))

        message = p.data_S

        global new_update_A
        global new_update_D

        if (self.name == "A" and new_update_A):
            #check to see if we're receiving a packet from router B
            if (int(message[5]) == 5):
                new_update_A = False
                cost = self.intf_L[2].cost + int(message[5])
                self.rt_tbl_D[3] = {2: (cost)}
                self.send_routes(1)

        elif (self.name == "D" and new_update_D):
            #check to see if we're receiving a packet from router C
            if (int(message[0]) == 3):
                new_update_D = False
                cost = self.intf_L[1].cost + int(message[0])
                self.rt_tbl_D[1] = {1: (cost)}
                self.send_routes(3)
        
    ## send out route update
    # @param i Interface number on which to send out a routing update
    def send_routes(self, i):
        message = Message(self.rt_tbl_D)

        p = NetworkPacket(0, 'control', 1, message.to_byte_S())

        if (self.name == "A"):
            neighbor1_intf = 2
            neighbor2_intf = 3

        elif (self.name == "B"):
            neighbor1_intf = 0
            neighbor2_intf = 1

        elif (self.name == 'C'):
            neighbor1_intf = 0
            neighbor2_intf = 1

        elif (self.name == 'D'):
            neighbor1_intf = 0
            neighbor2_intf = 1

        try:
            self.intf_L[neighbor1_intf].put(1, p.to_byte_S(), 'out', True)
            print('%s: sending routing update "%s" from interface %d' % (self, p, neighbor1_intf))

            self.intf_L[neighbor2_intf].put(1, p.to_byte_S(), 'out', True)
            print('%s: sending routing update "%s" from interface %d' % (self, p, neighbor2_intf))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass
        
    ## Print routing table
    def print_routes(self):
        print('%s: routing table' % self)
        rt_tbl_items = self.rt_tbl_D.items()
        rt_tbl_L = [["-", "-", "-"], ["-", "-", "-"], ["-", "-", "-"]]

        for host, intf_cost in rt_tbl_items:
            #router is utilizing 1 interface
            if (len(intf_cost) == 1):
                intf_cost = str(intf_cost)
                intf = str(intf_cost[1])
                cost = str(intf_cost[4])
                rt_tbl_L[int(intf)][host-1] = cost
            #router is utilizing 2 interfaces
            elif (len(intf_cost) == 2):
                intf_cost = str(intf_cost)
                intf1 = str(intf_cost[1])
                cost1 = str(intf_cost[4])
                intf2 = str(intf_cost[7])
                cost2 = str(intf_cost[10])

                rt_tbl_L[int(intf1)][host-1] = cost1
                rt_tbl_L[int(intf2)][host-1] = cost2

        interface0 = ' '.join(rt_tbl_L[0])
        interface1 = ' '.join(rt_tbl_L[1])
        interface2 = ' '.join(rt_tbl_L[2])

        print()
        print("       Cost to")
        print("       | 1 2 3")
        print("     --+------")
        print("     0 |", interface0)
        print("From 1 |", interface1)
        print("     2 |", interface2)
        print()
        
                
    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return 

class Message:
    def __init__(self, rt_tbl_D):
        self.rt_tbl_D = rt_tbl_D

    #convert routing table to a byte string for transmission over links
    def to_byte_S(self):
        rt_tbl_items = self.rt_tbl_D.items()
        rt_tbl_L = [["-", "-", "-"], ["-", "-", "-"], ["-", "-", "-"]]

        for host, intf_cost in rt_tbl_items:
            #router is utilizing 1 interface
            if (len(intf_cost) == 1):
                intf_cost = str(intf_cost)
                intf = str(intf_cost[1])
                cost = str(intf_cost[4])
                rt_tbl_L[int(intf)][host-1] = cost
            #router is utilizing 2 interfaces
            elif (len(intf_cost) == 2):
                intf_cost = str(intf_cost)
                intf1 = str(intf_cost[1])
                cost1 = str(intf_cost[4])
                intf2 = str(intf_cost[7])
                cost2 = str(intf_cost[10])

                rt_tbl_L[int(intf1)][host-1] = cost1
                rt_tbl_L[int(intf2)][host-1] = cost2

        interface0 = ''.join(rt_tbl_L[0])
        interface1 = ''.join(rt_tbl_L[1])
        interface2 = ''.join(rt_tbl_L[2])
        byte_S = interface0 + interface1 + interface2
        return byte_S