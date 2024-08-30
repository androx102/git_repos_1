import http.client as http
import json
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context
# login command body
commandBody = {"jsonrpc": "2.0",
               "method": "System.Users.Authenticate",
               "params": {
                   "userID": "root",
                   "password": "aptiv",
               },
               "id": 1
               }
 
# open connection
httpConnection = http.HTTPSConnection("192.168.110.1", timeout=10)
print(httpConnection)
 
# send login command
httpConnection.request('POST', '/jsonrpc', json.dumps(commandBody))
 
# get response for login command
response = httpConnection.getresponse()
print("Status: {} and reason: {}".format(response.status, response.reason))

# extract sessionID from login command response
respData = json.loads(response.read())
sessionID = respData["result"]["sessionID"]
print("SessionID: {}".format(sessionID))
 
# close connection
httpConnection.close()