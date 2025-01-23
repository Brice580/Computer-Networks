
High-Level Summary:

	The analysis_pcap_tcp code effectively parses the pcap file and reads the flows from the sender to the receiver caught on the wire. I utilize the dpkt library and a custom Python object to read the bytes from the file. I also leverage the seq and ack numbers of packets to calculate things like throughput, cwnd, etc. I also heavily utilize dictionaries to store various flows and values. After all calculations are completed, the correct output is displayed on the console.

Estimations:

	For part A, finding the flows was simply checking for SYN and FIN packets. Finding the 4 tuple was all about utilizing the dpkt lib. Finding the transactions was simply parsing the packets in the flow. The throughput was summing payload data bytes over a time period.

	For part B, I estimated RTT by sampling the time to receive an ACK after a certain packet was sent. I then skip the set up time and find the 3 first congestion windows that have take 1 RTT each. For calculating retransmissions from timeouts, I find the number of triple duplicate acks by checking if an ACK is received >2 times and then subtract that number by the total number of retransmissions.



Instructions:

Have python3 installed as well as dpkt library

Please open terminal and navigate to the directory where the .pcap file stored

Run the program by typing python3 assignment2.pcap, or whatever name .pcap file is

	The program will output the necessary output for both Parts A & B