import httplib
import json
import random
import socket
import thread
import time


class HttpClient():
    def __init__(self, baseAddress, port):
        self.baseAddress = baseAddress
        self.port = port

    def postJson(self, jsonMessage, url, callback=None):
        thread.start_new_thread(self.__postJson, ((jsonMessage, url, callback)))

    def callback(self, msg):
        print msg

    def __postJson(self, jsonMessage, url, callback):
        try:
            headers = {"Content-type": "application/json", "Accept": "text/plain"}
            conn = httplib.HTTPConnection(self.baseAddress, 8080)
            conn.request("POST", url, jsonMessage, headers)

            response = conn.getresponse()
            status = response.status
            data = response.read()

            conn.close()

            if callback is not None:
                callback(status)
        except socket.error:
            callback(-1)



if __name__ == "__main__":
    client = HttpClient("localhost", 8080)

    colors = ["#ffff00", "#00ff00", "#ff7400", "#0000ff", "#ff00ff", "#44aa55", "#000000"]

    while True:
        msg = {"command": {"color": random.choice(colors)}}
        client.postJson(json.dumps(msg), "/command")
        time.sleep(10)