#!/usr/bin/python3

import socket, re, pycurl, functools
from io import StringIO

from Logger import *

log = Logger(DEBUG)

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
      400 : 'Bad request'
      }
    return 'HTTP/1.1 %d %s' % (code, resps[code])
  
  @staticmethod
  def fromStr(txt):
    response = HttpResponse()
    tmp=txt.split('\n')
    first=tmp[0]
    regex = re.compile('HTTP\/\d\.\d (\d+) ')
    m = regex.match(first)
    code = int(m.group(1))

    response.setCode(code)
    
    tmp=tmp[1:]
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
    resp = self.getCodeString(self.code)+'\n'
    for key in self.headers:
      resp+="%s : %s\n" % (key, self.headers[key])

    resp+='\n'
    resp+=self.content
    resp = resp[:-1]
    return resp

class IO:
  def __init__(self):
    self.value=''

  def write(self, buf):
    self.value+=buf.decode()

  def reset(self):
    self.value=''

  def getvalue(self):
    return self.value

headers = IO()


def serveFrontPage():
    log(INFO, 'Serving frontpage')
    f = open('top.html', 'r')
    if not f:
        log(DEBUG, 'Serving frontpage as 404')
        http_response = """\
HTTP/1.1 404 Not found
Content-type: text/plain;charset=utf-8

Not found
"""
    else:
        log(DEBUG, 'Serving frontpage from file')
        top=f.read()
        http_response = """\
HTTP/1.1 200 Not found
Content-type: text/html;charset=utf-8

%s""" % (top)
    return http_response

def serveInfoPage(req):
    log(INFO, 'Serving infopage')
    response = HttpResponse()

    response.setCode(200)
    response.setHeader('Content', 'text/plain;charset=utf-8')

    txt=''
    for line in req:
        txt+=line
    response.setContent(txt)
    return response


c = pycurl.Curl()
c.setopt(c.HEADER, 1)
c.setopt(c.NOBODY, 1) # header only, no body
c.setopt(c.HEADERFUNCTION, headers.write)
c.setopt(pycurl.WRITEFUNCTION, lambda x: None)

class Unresolvable(Exception):
     def __init__(self, value):
         self.value = value
     def __str__(self):
         return repr(self.value)

#@lru_cache(maxsize=None)
#@functools.lru_cache(maxsize=100, typed=False)
@functools.lru_cache(maxsize=65536, typed=False)
def lookup(url, depth=0, maxDepth=10):
  headers.reset()
  log (DEBUG, "'%s'" % (url))
  c.setopt(c.URL, url)
  try:
    c.perform()
  except pycurl.error as e:
    if e.args[0]==6:
      raise Unresolvable(e.args[1])
    else:
      raise e

  hlines=headers.getvalue().split("\n")

#  print (hlines)
  resCode=int(hlines[0].split(' ')[1])
#  print (resCode)
  if (resCode in (301, 302, 307)):
    for hline in hlines:
      if hline.lower().startswith('location:'):
        target=hline.split(' ')[1]
        target=target.strip()
        return lookup(target, depth+1, maxDepth)
  log(DEBUG, url)
  return url


HOST, PORT = '', 8080

listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listen_socket.bind((HOST, PORT))
listen_socket.listen(1)
log (INFO, 'Serving HTTP on port %s ...' % PORT)
regex=re.compile('(GET|HEAD) \/(\S*)')
isURL=re.compile('https?:\/\/\S+')

while True:
  try:
    client_connection, client_address = listen_socket.accept()
    request = (client_connection.recv(8196)).decode()
    req=request.split("\n")
    log (DEBUG, 'First line is: ' + req[0])
    log (DEBUG, 'Request is: ' + str(req))
    m=regex.match(req[0])
    url=m.group(2)
    log (INFO, "Processing '%s'" % (url))

    if url == "":
      http_response = serveFrontPage()
    elif url == "info":
      http_response = serveInfoPage(req)
    else:
      if not isURL.match(url):
        nurl='http://'+url
        log (INFO, 'Rewriting %s to %s' % (url, nurl))
        url=nurl

      if log.shouldLog(DEBUG):
        hits=lookup.cache_info().hits
      l=lookup(url)
      if log.shouldLog(DEBUG):
        if lookup.cache_info().hits-hits>0:
          log(DEBUG, "Read from cache")
        else:
          log(DEBUG, "Cache miss")
        
      log(DEBUG, lookup.cache_info())

      res="%s -> %s" % (url, l)

      http_response = """\
HTTP/1.1 307 Temporary Redirect
Location: %s
Content-type: text/plain;charset=utf-8

%s
""" % (l, res)
  except Unresolvable as e:
    log (WARNING,'Unresolvable ' + str(e))
    http_response = """\
HTTP/1.1 400 Bad request
Content-type: text/plain;charset=utf-8

Bad request
"""
  except Exception as e:
    log (ERROR,'Unhandled error ' + str(e))
    http_response = HttpResponse()
    http_response.setCode(400)
    http_response.setHeader('Content-type' , 'text/plain;charset=utf-8')
    http_response.setContent('Bad request')

  resp=HttpResponse.fromStr(str(http_response))
  client_connection.sendall(str(resp).encode())
  client_connection.close()
