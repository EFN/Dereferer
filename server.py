#!/usr/bin/python3

import socket, re, pycurl, functools
from io import StringIO

from Logger import *
from HttpResponse import *
from IO import *

log = Logger(DEBUG)
headers = IO()


def serveFrontPage():
    log(INFO, 'Serving frontpage')
    response = HttpResponse()
    try:
        f = open('top.html', 'r')
        log(DEBUG, 'Serving frontpage from file')
        top=f.read()
        response.setCode(200)
        response.setHeader('Content', 'text/html;charset=utf-8')
        response.setContent(top)
        f.close()
    except:
        log(DEBUG, 'Serving frontpage as 404')
        response.setHeader('Content', 'text/plain;charset=utf-8')
        response.setCode(404)
        response.setContent('Not found')
    return response

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

      http_response = HttpResponse()
      http_response.setCode(307)
      http_response.setHeader('Content-type' , 'text/plain;charset=utf-8')
      http_response.setHeader('Location' , l)
      http_response.setContent(res)

  except Unresolvable as e:
    log (WARNING,'Unresolvable ' + str(e))
    http_response = HttpResponse()
    http_response.setCode(400)
    http_response.setHeader('Content-type' , 'text/plain;charset=utf-8')
    http_response.setContent('Bad request')
  except Exception as e:
    log (ERROR,'Unhandled error ' + str(e))
    http_response = HttpResponse()
    http_response.setCode(400)
    http_response.setHeader('Content-type' , 'text/plain;charset=utf-8')
    http_response.setContent('Bad request')

  client_connection.sendall(str(http_response).encode())
  client_connection.close()
