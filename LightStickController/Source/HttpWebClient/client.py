import httplib
import socket
import thread


class HttpClient():
    def __init__(self, baseAddress, port):
        self.baseAddress = baseAddress
        self.port = port

    def postJson(self, jsonMessage, url, callback=None):
        thread.start_new_thread(self._postJson, ((jsonMessage, url, callback)))

    def callback(self, msg):
        print msg

    def _postJson(self, jsonMessage, url, callback):
        try:
            headers = {"Content-type": "application/json", "Accept": "text/plain"}
            conn = httplib.HTTPConnection(self.baseAddress, 8080)
            conn.request("POST", url, jsonMessage, headers)

            response = conn.getresponse()
            status = response.status

            conn.close()

            if callback is not None:
                callback(status)
        except socket.error:
            callback(-1)
