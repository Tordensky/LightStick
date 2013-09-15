from config.serverconfig import APPLICATION_BASE_PATH, INDEX_HTML
from cmdhandler import CommandHandler
import libs.web as web


urls = (
    '/', 'index',
    '/command', 'command',
    '/(.*)', 'files'
)


class index:
    def GET(self):
        try:
            f = open(APPLICATION_BASE_PATH + INDEX_HTML, 'r')
            return f.read()

        except IOError:
            print "ERROR"
            return


class command:
    def GET(self):
        return web.cmdHandler.getCommand()

    def POST(self):
        web.cmdHandler.setCommand(web.data())
        return


class files:
    def GET(self, filename):
        try:
            f = open(APPLICATION_BASE_PATH + filename, 'r')
            return f.read()

        except IOError:
            print "ERROR"
            return


if __name__ == "__main__":
    web.cmdHandler = CommandHandler()
    app = web.application(urls, globals())
    app.run()
