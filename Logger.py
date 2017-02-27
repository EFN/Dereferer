#!/usr/bin/python3

import datetime
import time

DEBUG=1
INFO=2
WARNING=4
ERROR=8

class Logger:
    def __init__(self, lvl = INFO):
        self.DEBUGLEVEL = lvl


    def shouldLog(self, lvl = INFO):
          return (lvl >= self.DEBUGLEVEL)
        
    @staticmethod
    def errorcodeToString(code):
        if code == DEBUG:
            return 'DEBUG'
        if code == INFO:
            return 'INFO'
        if code == WARNING:
            return 'WARNING'
        if code == ERROR:
            return 'ERROR'

    def __call__(self,LEVEL, txt):
          if LEVEL >= self.DEBUGLEVEL:
                ts = time.time()
                st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                print ('%s %-7s: %s' % (st, self.errorcodeToString(LEVEL), str(txt)))

if __name__ == '__main__':
    log=Logger(DEBUG)
    log(DEBUG, 'hei')


