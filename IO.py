#!/usr/bin/python3

class IO:
  def __init__(self):
    self.value=''

  def write(self, buf):
    self.value+=buf.decode()

  def reset(self):
    self.value=''

  def getvalue(self):
    return self.value

