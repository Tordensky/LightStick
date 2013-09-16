import httplib
import json


class HttpClient():
    def __init__(self, baseAddress, port):
        self.baseAddress = baseAddress
        self.port = port

    def postJson(self, jsonMessage, url):
        headers = {"Content-type": "application/json", "Accept": "text/plain"}
        conn = httplib.HTTPConnection(self.baseAddress, 8080)
        conn.request("POST", url, jsonMessage, headers)
        response = conn.getresponse()

        print response.status
        print response.read()

        conn.close

if __name__ == "__main__":
    client = HttpClient("localhost", 8080)
    msg = {"command": {"color": "#ff0000"}}
    client.postJson(json.dumps(msg), "/command")