import httplib
import json
import random
import time


class HttpClient():
    def __init__(self, baseAddress, port):
        self.baseAddress = baseAddress
        self.port = port

    def postJson(self, jsonMessage, url):
        headers = {"Content-type": "application/json", "Accept": "text/plain"}
        conn = httplib.HTTPConnection(self.baseAddress, 8080)
        conn.request("POST", url, jsonMessage, headers)
        #response = conn.getresponse()

        #print response.status
        #print response.read()

        conn.close()

if __name__ == "__main__":
    client = HttpClient("localhost", 8080)

    colors = ["#ffff00", "#00ff00", "#ff7400", "#0000ff", "#ff00ff", "#44aa55", "#000000"]

    while True:
        msg = {"command": {"color": random.choice(colors)}}
        client.postJson(json.dumps(msg), "/command")
        #time.sleep(0.1)