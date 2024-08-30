#!/usr/bin/env python3
import http.client as httplib
import time
import json
import sys


USERNAME = 'root'
PASSWORD = 'aptiv'


def https_connection():
    import ssl
    return httplib.HTTPConnection(server_address, context=ssl._create_unverified_context())


class JsonRPCException(Exception):
    pass


class Flow:
    def __init__(self, server_address):
        self.connection = httplib.HTTPConnection(server_address)
        self.session_id = None
        self.counter = 1

    def __call__(self, command):
        """
        Call a Flow JsonRPC function, adding the "jsonrpc" and "id"
        fields automatically. Raises JsonRPCException on error.

        Returns response data from the server.
        """
        command["jsonrpc"] = "2.0"
        if 'id' not in command:
            command["id"] = self.counter
            self.counter += 1

        self.connection.request('POST', '/jsonrpc', json.dumps(command))
        response = self.connection.getresponse()

        if response.status != 200:
            raise JsonRPCException(f'{response.status} {response.reason}')

        data = json.loads(response.read())
        if 'error' in data:
            raise JsonRPCException(data['error']['message'])

        return data['result']

    def jsonrpc_version(self):
        return self({
            "method": "JSONRPC.Version",
            "params": {}
        })

    def login(self, user=USERNAME, passwd=PASSWORD):
        response = self({
            "method": "System.Users.Authenticate",
            "params": {
                "userID": user,
                "password": passwd
            }
        })
        self.session_id = response['sessionID']
        return response

    def stepped_initialize(self, positions, start_position=0):
        return self({
            "method": "Chamber.Stirring.Stepped.Initialize",
            "params": {
                "sessionID": self.session_id,
                "positions": positions,
                "settings": {
                    "init_mode": "normal",
                    "address": start_position,
                    "enable_turntable": True
                }
            }
        })

    def stepped_next_pos(self):
        return self({
            "method": "Chamber.Stirring.Stepped.NextPos",
            "params": { "sessionID": self.session_id }
        })


if __name__ == '__main__':
    #for server_address in sys.argv[1:]:
        flow_api = Flow("192.168.110.1")
        flow_api.login()
        print("x")
       # flow_api.stepped_initialize(positions=200, start_position=8)
