from cmdhandler import CommandHandler
import web

urls = (
    '/', 'index'
)

cmdHandler = CommandHandler()


class index:
    def GET(self):
        return cmdHandler.getCommand()

    def POST(self):
        cmdHandler.setCommand(web.data())
        return


if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()

