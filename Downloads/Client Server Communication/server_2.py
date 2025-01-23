'''
This module defines the behaviour of server in your Chat Application
'''
import sys
import getopt
import socket
import util



class Server:
    '''
    This is the main Server Class. You will  write Server code inside this class.
    '''
    def __init__(self, dest, port, window):
        self.client_map = {} #Client map to store client and address tuples
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(None)
        self.sock.bind((self.server_addr, self.server_port))

    def start(self):
        '''
        Main loop.
        Continue receiving messages from Clients and processing them
        '''
        while True:
            try:
                data, addr = self.sock.recvfrom(2048)
                if data:
                    self.handle_packet(data, addr)
            except Exception as e:
                print(f"Error receiving data: {e}")

    def handle_packet(self, data, addr):
        '''
        Handles incoming packets and has dedicated helpers for each data packet
        '''
        decoded_data = data.decode()
        msg_type, seqno, message, checksum = util.parse_packet(decoded_data)
        
        if util.validate_checksum(decoded_data) and msg_type == 'data':
            component = message.split()
            command = component[0]
            
            if command == "join":
                self.handle_join(component, addr)
            elif command == "request_users_list":
                self.handle_user_list_request(addr)
            elif command == "disconnect":
                self.handle_disconnect(component)
            elif command == "send_message":
                self.handle_send_message(component, addr)
            else:
                self.handle_unknown_message(component, addr)


    def handle_join(self, component, addr):
        '''
        JOIN data packet handler, checks the cases and connects user
        '''
        if len(self.client_map) >= util.MAX_NUM_CLIENTS:
            self.send_error("err_server_full", addr)
            print("disconnected: server full\n")
        elif component[2] in self.client_map:
            self.send_error("err_username_unavailable", addr)
            print("disconnected: username not available\n")
        else:
            username = component[2]
            self.client_map[username] = addr
            print(f"join: {username}\n")

    def handle_user_list_request(self, addr):
        '''
        LIST data packet handler, sends a list based on client mapping
        '''
        users_list = " ".join(self.client_map.keys())
        self.send_response("response_users_list", 3, users_list, addr)
        username = self.get_username_by_addr(addr)
        print(f"request_users_list: {username}\n")

    def handle_disconnect(self, component):
        '''
        DISCONNECT data packet handler, remove from client mapping
        '''
        username = component[2]
        if username in self.client_map:
            del self.client_map[username]
            print(f"disconnected: {username}\n")

    def handle_send_message(self, component, addr):
        '''
        Handles sending messages to specified users, forwards msg
        '''
        command_part = component[2:]
        users = int(command_part[0])
        usernames = command_part[1:1 + users]
        message = " ".join(command_part[1 + users:])
        unique_usernames = list(set(usernames))

        sender_username = self.get_username_by_addr(addr)
        print(f"msg: {sender_username}\n")

        for name in unique_usernames:
            if name not in self.client_map:
                print(f"msg: {sender_username} to non-existent user {name}\n")
            else:
                self.forward_message(sender_username, message, name)

    def handle_unknown_message(self, addr):
        '''
        Handles unknown messages from clients, deletes users
        '''
        username = self.get_username_by_addr(addr)
        if username:
            print(f"disconnected: {username} sent unknown command")
            self.send_error("err_unknown_message", addr)
            if username in self.client_map:
                del self.client_map[username]

    def send_error(self, error_type, addr):
        '''
        Error handling helper to make error pkt
        '''
        error_msg = util.make_message(error_type, 2)
        err_packet = util.make_packet("data", 0, error_msg)
        self.sock.sendto(err_packet.encode(), addr)

    def send_response(self, message_type, message_code, message, addr):
        '''
        Response handler, for sending data back to client
        '''
        response = util.make_message(message_type, message_code, message)
        packet = util.make_packet("data", 0, response)
        self.sock.sendto(packet.encode(), addr)

    def forward_message(self, sender_username, message, recipient_username):
        '''
        Forwards a message to the specified user
        '''
        client_str = f"msg: {sender_username}: {message}\n"
        forward_msg = util.make_message("forward_message", 4, client_str)
        fwd_packet = util.make_packet("data", 0, forward_msg)
        self.sock.sendto(fwd_packet.encode(), self.client_map[recipient_username])

    def get_username_by_addr(self, addr):
        '''
        Retrieves the username associated with the given address
        '''
        for name, address in self.client_map.items():
            if address == addr:
                return name
        return ''
                
# Do not change below part of code

if __name__ == "__main__":
    def helper():
        '''
        This function is just for the sake of our module completion
        '''
        print("Server")
        print("-p PORT | --port=PORT The server port, defaults to 15000")
        print("-a ADDRESS | --address=ADDRESS The server ip or hostname, defaults to localhost")
        print("-w WINDOW | --window=WINDOW The window size, default is 3")
        print("-h | --help Print this help")

    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:],
                                   "p:a:w", ["port=", "address=","window="])
    except getopt.GetoptError:
        helper()
        exit()

    PORT = 15000
    DEST = "localhost"
    WINDOW = 3

    for o, a in OPTS:
        if o in ("-p", "--port="):
            PORT = int(a)
        elif o in ("-a", "--address="):
            DEST = a
        elif o in ("-w", "--window="):
            WINDOW = a

    SERVER = Server(DEST, PORT,WINDOW)
    try:
        SERVER.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
