
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

def run():
    server_address = ('0.0.0.0', 3000)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print('Server running at http://0.0.0.0:3000/')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
