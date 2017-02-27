#!/usr/bin/python3

import re

class HttpResponse:
  def __init__(self):
    self.headers={}
    self.content=''
    self.code = 0

  def setCode(self, code):
    self.code = code

  def setHeader(self, key, value):
    self.headers[key]=value

  def setContent(self, content):
    self.content=content

  @staticmethod
  def getCodeString(code):
    resps={
      200 : 'OK',
      307 : 'Temporary Redirect',
      400 : 'Bad request',
      404 : 'Not found'
      }
    return 'HTTP/1.1 %d %s' % (code, resps[code])
  
  @staticmethod
  def fromStr(txt):
    response = HttpResponse()
    tmp=txt.split('\n')
    first = tmp[0]
    regex = re.compile('HTTP\/\d\.\d (\d+) ')
    m = regex.match(first)
    code = int(m.group(1))

    response.setCode(code)
    
    tmp = tmp[1:]
    beginning=True
    for t in tmp:
      if beginning and t=='':
        beginning=False
      elif beginning:
        regex = re.compile('([^:]+)\s*:\s*(.*)')
        m = regex.match(t)
        key = m.group(1)
        value = m.group(2)
        response.setHeader(key,value)
      else:
        response.content+=t+'\n'
    return response

  def __str__(self):
    resp = self.getCodeString(self.code) + '\n'
    for key in self.headers:
      resp+="%s : %s\n" % (key, self.headers[key])

    resp += '\n'
    resp += self.content
    return resp
