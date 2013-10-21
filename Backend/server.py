from config.serverconfig import APPLICATION_BASE_PATH, INDEX_HTML
from cmdhandler import CommandHandler, MsvController, FileCash
import libs.web as web


urls = (
    '/', 'index',
    '/command', 'command',
    '/(.*)', 'files'
)


class index:
    def GET(self):
        raise web.seeother('/static/MsvClient/Html/index.html')

        # try:
        #     f = open(APPLICATION_BASE_PATH + INDEX_HTML, 'r')
        #     return f.read()
        #
        #
        # except IOError, e:
        #     print "ERROR", e
        #     return


class command:
    def GET(self):
        return web.cmdHandler.getCommand()

    def POST(self):
        web.cmdHandler.setCommand(web.data())
        return


class files:
    def GET(self, filename):
        try:
            #f = open(APPLICATION_BASE_PATH + filename, 'rb')
            #return f.read()

            return web.cache.getFile(filename)
        except IOError, e:
            print "ERROR", e
            return


if __name__ == "__main__":
    web.cmdHandler = CommandHandler()
    web.cache = FileCash()
    app = web.application(urls, globals())
    app.run()

