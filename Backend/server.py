import json
from cmdhandler import Monitor
from cmdhandler import CommandHandler, FileCash
import libs.web as web


urls = (
    '/', 'index',
    '/command', 'command',
    '/(.*)', 'files'
)


class index:
    def GET(self):
        raise web.seeother('/static/MsvClient/Html/index.html')


class command:
    def GET(self):
        params = web.input()

        if "id" in params:
            web.heartBeatMonitor.addID(params.id)

        return web.cmdHandler.getCommand()

    def POST(self):
        web.cmdHandler.setCommand(json.loads(web.data()))
        return


# class files:
#     def GET(self, filename):
#         try:
#             #f = open(APPLICATION_BASE_PATH + filename, 'rb')
#             #return f.read()
#
#             return web.cache.getFile(filename)
#         except IOError, e:
#             print "ERROR", e
#             return


if __name__ == "__main__":
    web.cmdHandler = CommandHandler()
    web.heartBeatMonitor = Monitor()
    web.cache = FileCash()
    app = web.application(urls, globals())
    app.run()

