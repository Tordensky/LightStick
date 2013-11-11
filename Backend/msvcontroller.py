from libs.pymsv.msvclient.client import Client, Msv


class MsvController():
    def __init__(self, host, msv_id):
        self.HOST = host
        self.MSV_ID = msv_id

        # TODO normally crashes on first startup, give more tries to start msv service
        try:
            self._client = Client(self.HOST)
            self._client.start()
            self._msv = Msv(self._client, self.MSV_ID)

        except AssertionError:
            print "! ! ! ERROR, FAILED TO LOAD MSV ! ! !"

    def set_msv_value(self, value):
        self._update(value)

    def get_current_msv_value(self):
        return int(self._msv.query()[0])

    def _update(self, value):
        msv_data_list = [{'msvid': self.MSV_ID,
                          'vector': (value, 0.0, 0.0)}]
        self._client.update(msv_data_list)

    def add_update_handler(self, update_handler):
        self._msv.add_handler(update_handler)
