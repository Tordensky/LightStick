import logging
import logging.handlers

class Singleton(object):
  _instance = None
  def __new__(class_, *args, **kwargs):
    if not isinstance(class_._instance, class_):
        class_._instance = object.__new__(class_, *args, **kwargs)
    return class_._instance

class MyLog(Singleton):
    def __init__(self):
        self.log = logging.getLogger("MSV")
        if len(self.log.handlers) == 0:
          hdlr = logging.handlers.RotatingFileHandler("msv.log",
                                                      maxBytes=42*1024*1024)
          formatter = logging.Formatter('%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s')
          hdlr.setFormatter(formatter)
          self.log.addHandler(hdlr)
          self.log.setLevel(logging.DEBUG)
        
        
        
