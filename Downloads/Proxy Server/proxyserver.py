import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create socket
port = 8080 #not a reserved port
server_socket.bind(('127.0.0.1', port)) #127.0.0.1 is local host
server_socket.listen(1) #max number of queued connections
print("Server connected and listening on port: ", port)
proxy_cache = {}

while True:
    
    try:

        client_socket, addr = server_socket.accept() #waits for accept
        print("Connection accepted from:", addr)

        #now handle/parse the request 
        req = client_socket.recv(1024).decode() 
    
        content = req.split('\r\n')[0].split(' ')
        server = content[1] #this will be in the form /www.xxx.com ?

        if server.startswith("/http://"): #http case
            print("here")
            hostname = server.split('/')[3]
            pathname =  '/'.join(server.split('/')[4:])
            print(hostname, pathname)

        else: #www. case

            hostname = server.split('/')[1]
            pathname = '/'.join(server[1:].split('/')[1:])
            print(hostname, pathname)

        if server[1:] in proxy_cache:
            # webpage is already cached so no need to connect to the webserver
            print("Retreiving response from cache")
            client_socket.sendall(proxy_cache[server[1:]])
        else:
            #server is not in cache so send a request to the server
            #open a socket to the webserver from the client
            #send the req and get response
            #cache the response
            #send response to client

            web_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            web_socket.connect((hostname, 80)) #http works on port 80 for some reason

            request = "GET /"
            request += pathname + " "
            request += "HTTP/1.0\r\n"
            request += "Host: " + hostname + "\r\n\r\n"

            print("Sending request to web server:\n ", request)
            web_socket.sendall(request.encode())

            #now get the response from the server and make sure its 200 to cache it!
            res = b""
            while 1:
                bytes_read = web_socket.recv(1024)
                
                
                if len(bytes_read) != 0:
                    res += bytes_read #append
                    
                else:
                    
                    break
            
            #response is now stored, check if its 200 to store it!
            res_content = res.split(b"\r\n")[0]
            status = res_content.split()[1]
            print('Status: ', status)

            if status == b'200':
                #add to cache
                proxy_cache[server[1:]] = res #map the url to the response?
                print("Added to cache")
            
            web_socket.close()
            client_socket.sendall(res)
            
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