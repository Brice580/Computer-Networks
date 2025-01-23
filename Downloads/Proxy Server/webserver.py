import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create socket
port = 8080 #not a reserved port
server_socket.bind(('127.0.0.1', port)) #127.0.0.1 is local host
server_socket.listen(1) #max number of queued connections
print("Server connected and listening on port: ", port)

while True:
    
    try:

        client_socket, addr = server_socket.accept() #waits for accept
        req = client_socket.recv(1024).decode() #this is the http request - read the file
        req_content = req.split('\r\n')[0].split(' ')
        file = req_content[1]
        file_name = file[1::]
        print(req)

        with open(file_name, 'rb') as file:
            content = file.read() #reading binary bytes

        response = "HTTP/1.1 200 OK\r\n"
        response += "\r\n"
        response = response.encode() + content #content is already encoded

        client_socket.sendall(response)

    except FileNotFoundError:
        #send 404 error

        response = "HTTP/1.1 404 Not Found\r\n"
        response += "Content-Type: text/html\r\n"
        response += "Content-Length: 53\r\n\r\n"
        response += "<html><body><h1>404 Page Not Found</h1></body></html>"
        
        client_socket.send(response.encode())

    except Exception as e:
        print(e)



    client_socket.close()
    