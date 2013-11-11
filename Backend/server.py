import json
from logger import Logger
from cmdhandler import CommandHandler
import libs.web as web

urls = (
    '/', 'index',
    '/command', 'command'
)


class index:
    def GET(self):
        raise web.seeother('/static/MsvClient/Html/index.html')


class command:
    def GET(self):
        params = web.input()

        if "id" in params:
            web.heart_beat_monitor.add_log_id(params.id)

        return web.cmd_handler.get_current_command()

    def POST(self):
        web.cmd_handler.set_current_command(json.loads(web.data()))
        return

if __name__ == "__main__":
    web.cmd_handler = CommandHandler()
    web.heart_beat_monitor = Logger()
    web.heart_beat_monitor.start_logger()
    app = web.application(urls, globals())
    app.run()
