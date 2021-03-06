#!/usr/bin/python
import time
import pynvc

messages_in_progress = {}

pynvc.init(0)
while(True):
  src, message = pynvc.receive(1000)
  if message == None:
    continue
  command = message[0]
  debugtext = ''.join(chr(i) for i in message[1:])
  #print '%d %d "%s"' % (command, len(debugtext), debugtext)
  if command == pynvc.DEBUG_TRACE_PART:
    if not messages_in_progress.has_key(src):
      messages_in_progress[src] = ""
    messages_in_progress[src] += debugtext
  elif command == pynvc.DEBUG_TRACE_FINAL:
    if messages_in_progress.has_key(src):
      debugtext = messages_in_progress[src] + debugtext
      messages_in_progress[src] = ""
    print ("[%s node %d] %s" % (time.strftime("%H:%M:%S ", time.localtime()), src, debugtext.rstrip()))
