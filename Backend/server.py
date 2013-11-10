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
            web.heartBeatMonitor.log_id(params.id)

        return web.cmdHandler.getCommand()

    def POST(self):
        web.cmdHandler.setCommand(json.loads(web.data()))
        return

if __name__ == "__main__":
    web.cmdHandler = CommandHandler()
    web.heartBeatMonitor = Logger()
    web.heartBeatMonitor.start_logger()
    app = web.application(urls, globals())
    app.run()
