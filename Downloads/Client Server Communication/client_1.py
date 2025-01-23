'''
This module defines the behaviour of a client in your Chat Application
'''

import sys
import getopt
import socket
import random
from threading import Thread
import os
import util

class Client:
    '''
    This is the main Client Class.
    '''
    def __init__(self, username, dest, port, window_size):
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(None)
        self.sock.bind(('', random.randint(10000, 40000)))
        self.name = username
        self.active = True
        self.addr_tuple = (self.server_addr, self.server_port)

    def send_packet(self, message_type, message_code, message):
        '''
        Create and and send data packets
        '''
        packet_message = util.make_message(message_type, message_code, message)
        packet = util.make_packet("data", 0, packet_message)
        self.sock.sendto(packet.encode(), self.addr_tuple)

    def handle_command(self, action):
        '''
        This function handles the "commands" of the user which is the input
        '''
        command_parts = action.split()
        command = command_parts[0].lower()

        if command == 'quit':
            self.send_packet("disconnect", 1, self.name)
            print("quitting\n")
            self.active = False
            self.sock.close()
        
        elif command == 'list':
            self.send_packet("request_users_list", 2, "")
        
        elif command == 'msg':
            if len(command_parts) >= 4:
                commands = " ".join(command_parts[1:])
                self.send_packet("send_message", 4, commands)
        
        elif command == "help":
            self.print_help()
        
        else:
            print("incorrect userinput format\n")

    def print_help(self):
        '''
        Prints help information
        '''
        helper = """
            Commands:
            1) Message:
            Input: msg <number_of_users> <username1> <username2> ... <message>
            2) Available Users:
            Input: list
            3) Help:
            Input: help
            4) Quit:
            Input: quit\n
            """
        print(helper)

    def start(self):
        '''
        Main Loop is here
        Start by sending the server a JOIN message. 
        Use make_message() and make_util() functions from util.py to make your first join packet
        Waits for user input and then process it
        '''
        self.send_packet("join", 1, self.name)
        
        while self.active:
            try:
                action = input()
                self.handle_command(action)
            except KeyboardInterrupt:
                break

    def process_received_message(self, data):
        '''
        This function processes any incoming communcation and parses packets
        '''
        decoded_data = data.decode()
        msg_type, seqno, message, checksum = util.parse_packet(decoded_data)

        if util.validate_checksum(decoded_data) and msg_type == 'data':
            component = message.split()

            if component[0] == 'err_server_full':
                print("disconnected: server full\n")
                self.active = False
                self.sock.close()
                os._exit(0)
            
            elif component[0] == 'err_username_unavailable':
                print("disconnected: username not available\n")
                self.active = False
                self.sock.close()
                os._exit(0)

            elif component[0] == 'response_users_list':
                usernames = component[2:]
                usernames.sort()
                print(f"list: {' '.join(usernames)}\n")

            elif component[0] == 'forward_message':
                text = " ".join(component[2:])
                print(text)

            elif component[0] == 'err_unknown_message':
                print("disconnected: server received an unknown command\n")
                self.shutdown_client()

    def receive_handler(self):
        '''
        Loop that waits fot data from the server and handles it
        '''
        while self.active:
            try:
                data, addr = self.sock.recvfrom(2048)
                if data:
                    self.process_received_message(data)
            except Exception as e:
                print("")

# Do not change below part of code
if __name__ == "__main__":
    def helper():
        '''
        This function is just for the sake of our Client module completion
        '''
        print("Client")
        print("-u username | --user=username The username of Client")
        print("-p PORT | --port=PORT The server port, defaults to 15000")
        print("-a ADDRESS | --address=ADDRESS The server ip or hostname, defaults to localhost")
        print("-w WINDOW_SIZE | --window=WINDOW_SIZE The window_size, defaults to 3")
        print("-h | --help Print this help")

    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:], "u:p:a:w", ["user=", "port=", "address=", "window="])
    except getopt.error:
        helper()
        exit(1)

    PORT = 15000
    DEST = "localhost"
    USER_NAME = None
    WINDOW_SIZE = 3
    for o, a in OPTS:
        if o in ("-u", "--user="):
            USER_NAME = a
        elif o in ("-p", "--port="):
            PORT = int(a)
        elif o in ("-a", "--address="):
            DEST = a
        elif o in ("-w", "--window="):
            WINDOW_SIZE = a

    if USER_NAME is None:
        print("Missing Username.")
        helper()
        exit(1)

    S = Client(USER_NAME, DEST, PORT, WINDOW_SIZE)
    try:
        # Start receiving Messages
        T = Thread(target=S.receive_handler)
        T.daemon = True
        T.start()
        # Start Client
        S.start()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
