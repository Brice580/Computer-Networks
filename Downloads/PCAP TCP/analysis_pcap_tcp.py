import dpkt


class Flow:
    def __init__(self, source_port, source_ip, dest_port, dest_ip, seq, ack, syn_ts, fin_ts):
        self.source_port = source_port
        self.source_ip = source_ip
        self.dest_port = dest_port
        self.dest_ip = dest_ip
        self.seq = seq
        self.ack = ack
        self.syn_ts = syn_ts
        self.fin_ts = fin_ts
        self.packet_count = 0
        self.complete = False
        self.transactions = []
        self.throughput = 0
        self.length = 0
        self.rtt = 0
        self.cwnds = []
        self.seq = {}
        self.ack = {}
        self.triple = 0
        self.timeouts = 0


def pcap_analysis(pcap_file):

    mapping = {}
    sender = "130.245.145.12"
    reciever = "128.208.2.198"

    with open(pcap_file, 'rb') as file:
        pcap = dpkt.pcap.Reader(file)
        for ts, buf in pcap:
            ethernet = dpkt.ethernet.Ethernet(buf) #breaks it down into parts we want

            packet_ip = ethernet.data

            if packet_ip.p != dpkt.ip.IP_PROTO_TCP: #ignoring packets not TCP
                continue
            
            tcp = packet_ip.data #tcp header

            if (tcp.flags & dpkt.tcp.TH_SYN and not (tcp.flags & dpkt.tcp.TH_ACK)):
                #beginning of a flow
                key = (tcp.sport, packet_ip.src, tcp.dport, packet_ip.dst)
                
                mapping[key] = Flow(tcp.sport, dpkt.utils.inet_to_str(packet_ip.src), 
                            tcp.dport, dpkt.utils.inet_to_str(packet_ip.dst),tcp.seq, tcp.ack,
                            ts, None)

            elif tcp.flags & dpkt.tcp.TH_FIN:
                #end of flow
                key = (tcp.sport, packet_ip.src, tcp.dport, packet_ip.dst)
                if key in mapping:
                    mapping[key].fin_ts = ts

            else:
                key = (tcp.sport, packet_ip.src, tcp.dport, packet_ip.dst)
                if key in mapping:
                    flow = mapping[key]
                    if not flow.complete:
                        if flow.packet_count < 2:

                            scale = 2**tcp.opts[4]

                            if (tcp.seq, tcp.ack, tcp.win * scale ) not in flow.transactions:
                                flow.transactions.append((tcp.seq, tcp.ack, tcp.win * scale))
                                flow.packet_count += 1
                                if flow.packet_count == 2:
                                    flow.complete = True

        
        
        calc_throughput(mapping)

        calc_congestion_win(mapping)

        find_retransmissions(mapping)

        print("There are",len(mapping.keys()), "flows initiated")
        print()
        print_flow_details(mapping)


def find_retransmissions(mapping):
    for flow_key, flow_obj in mapping.items():
        triple_duplicate_ack_count = 0
        retransmits = 0


        with open("assignment2.pcap", 'rb') as file:
            pcap = dpkt.pcap.Reader(file)
            for ts, buf in pcap:
                ethernet = dpkt.ethernet.Ethernet(buf)
                packet_ip = ethernet.data

                # Check if the packet is TCP and belongs to the current flow
                if packet_ip.p != dpkt.ip.IP_PROTO_TCP:
                    continue

                tcp = packet_ip.data

                # Check if the packet belongs to the current flow
                if packet_ip.data.sport == flow_obj.source_port and \
                   packet_ip.data.dport == flow_obj.dest_port and \
                   dpkt.utils.inet_to_str(packet_ip.src) == flow_obj.source_ip and \
                   dpkt.utils.inet_to_str(packet_ip.dst) == flow_obj.dest_ip:

                   flow_obj.seq[tcp.seq] = flow_obj.seq.get(tcp.seq, 0) + 1 #store the freq of Seq #'s for each flow
                

            #loop through values to see how many retransmits (freq > 1)
            for seq_number, counter in flow_obj.seq.items():
                if counter > 1:
                    retransmits += 1
            
            for ts, buf in pcap:
                ethernet = dpkt.ethernet.Ethernet(buf)
                packet_ip = ethernet.data

                # Check if the packet is TCP and belongs to the current flow
                if packet_ip.p != dpkt.ip.IP_PROTO_TCP:
                    continue

                tcp = packet_ip.data

                if packet_ip.data.sport == flow_obj.dest_port and \
                   packet_ip.data.dport == flow_obj.source_port and \
                   dpkt.utils.inet_to_str(packet_ip.src) == flow_obj.dest_ip and \
                   dpkt.utils.inet_to_str(packet_ip.dst) == flow_obj.source_ip:

                   flow_obj.ack[tcp.ack] = flow_obj.ack.get(tcp.ack, 0) + 1 #store the freq of Seq #'s for each flow

            for ack_number, counter in flow_obj.ack.items():
                if counter > 2:
                    triple_duplicate_ack_count += 1       

                    
           
            flow_obj.timeouts = retransmits - triple_duplicate_ack_count
            flow_obj.triple = triple_duplicate_ack_count 



def calc_congestion_win(mapping):

    
    for flow_key, flow_obj in mapping.items():
        
        packets_in_flow = []
        packet_after_syn = None
        start_time = None
        end_time = None
        
        with open("assignment2.pcap", 'rb') as file:
            pcap = dpkt.pcap.Reader(file)
            for ts, buf in pcap:
                ethernet = dpkt.ethernet.Ethernet(buf)
                packet_ip = ethernet.data
                
                # Check if the packet is TCP and belongs to the current flow
                if packet_ip.p != dpkt.ip.IP_PROTO_TCP:

                    continue

             
                #flow_obj is essentially the SYN packet
                if packet_ip.data.sport == flow_obj.source_port and \
                   packet_ip.data.dport == flow_obj.dest_port and \
                   dpkt.utils.inet_to_str(packet_ip.src) == flow_obj.source_ip and \
                   dpkt.utils.inet_to_str(packet_ip.dst) == flow_obj.dest_ip:
                    
                    tcp = packet_ip.data
                    packets_in_flow.append((ts, tcp))
                    
                    
                    if len(packets_in_flow) == 4:  #randomly pick the 4th packet to test for RTT
                        packet_after_syn = tcp
                        start_time = ts
                        
                        break  


            #NOW that the packet is found, we want to find the ACK 

            if packet_after_syn is not None:
            
                ack_for_packet_after_syn = None

              
                for ts, buf in pcap:
                    ethernet = dpkt.ethernet.Ethernet(buf)
                    packet_ip = ethernet.data
                    
                    # Check if the packet is TCP and is going from reciever to sender (ACK)
                    if packet_ip.p == dpkt.ip.IP_PROTO_TCP and \
                    packet_ip.data.sport == flow_obj.dest_port and \
                    packet_ip.data.dport == flow_obj.source_port and \
                    dpkt.utils.inet_to_str(packet_ip.src) == flow_obj.dest_ip and \
                    dpkt.utils.inet_to_str(packet_ip.dst) == flow_obj.source_ip:
                        
                        tcp = packet_ip.data
                        
                        # Check if the packet is an ACK for the desired packet
                        if tcp.seq == packet_after_syn.ack:
                            ack_for_packet_after_syn = tcp
                            end_time = ts
                            flow_obj.rtt = end_time - start_time
                            
                            break

            #Now We have the RTT's of each flow, calculate the cwnds
        packets_sent = 0
        
        # Calculate RTTs

        first = flow_obj.rtt*2 +flow_obj.syn_ts #skip the set up syn ack fin

        counter1 = 0
        counter2 = 0
        counter3 = 0
        
        with open("assignment2.pcap", 'rb') as file:
            pcap = dpkt.pcap.Reader(file)
            for ts, buf in pcap:
                ethernet = dpkt.ethernet.Ethernet(buf)
                packet_ip = ethernet.data
                
                # Check if the packet belongs to the current flow
                if packet_ip.p == dpkt.ip.IP_PROTO_TCP and \
                   packet_ip.data.sport == flow_obj.source_port and \
                   packet_ip.data.dport == flow_obj.dest_port and \
                   dpkt.utils.inet_to_str(packet_ip.src) == flow_obj.source_ip and \
                   dpkt.utils.inet_to_str(packet_ip.dst) == flow_obj.dest_ip:
                    
                    #Check if the packet's timestamp falls within the RTT window
                    if ts <= first and ts > flow_obj.syn_ts:
                        counter1 += 1
                    elif ts <= first + flow_obj.rtt and ts > first:
                        counter2 += 1
                    elif ts <= first + flow_obj.rtt + flow_obj.rtt and ts > first + flow_obj.rtt:
                        counter3 += 1
                        
                        
        
            flow_obj.cwnds = [counter1, counter2, counter3]



       



def calc_throughput(mapping):

    with open("assignment2.pcap", 'rb') as file:
        pcap = dpkt.pcap.Reader(file)
        for ts, buf in pcap:
            ethernet = dpkt.ethernet.Ethernet(buf) #breaks it down into parts we want

            packet_ip = ethernet.data

            if packet_ip.p != dpkt.ip.IP_PROTO_TCP: #ignoring packets not TCP
                continue
            
            tcp = packet_ip.data

            key = (tcp.sport, packet_ip.src, tcp.dport, packet_ip.dst)
            if key in mapping:
                flow = mapping[key] #gets the correct corresponding flow

                #sum up data packets from SYN to FIN in length field of flow...
                flow.length += len(tcp.data) #increment length

        #Loop through the map and calculate throughput of each flow using length and timestamps of syn and fin

        for flow_key, flow_obj in mapping.items():
            total_data_sent = flow_obj.length 
            start_time = flow_obj.syn_ts 
            end_time = flow_obj.fin_ts 

            time = end_time - start_time

            flow_obj.throughput = total_data_sent / time


 
def print_flow_details(mapping):
    counter = 1
    for flow_key, flow_obj in mapping.items():
        print("Flow:", counter)
        counter += 1
        print("Source IP:", flow_obj.source_ip)
        print("Source Port:", flow_obj.source_port)
        print("Destination IP:", flow_obj.dest_ip)
        print("Destination Port:", flow_obj.dest_port)
        print("Throughput:", flow_obj.throughput, "bytes/sec")
        print("Congestion Window:", flow_obj.cwnds)
        print("# of Triple Dup Ack:", flow_obj.triple)
        print("# of Timeouts:", flow_obj.timeouts)

        print("Transactions:")
        print()
        for i, transaction in enumerate(flow_obj.transactions):
            print(f"Transaction {i + 1}:")
            print("Sequence Number:", transaction[0])
            print("Acknowledgment Number:", transaction[1])
            print("Receive Window Size:", transaction[2])
            print()
    
pcap_analysis('assignment2.pcap')