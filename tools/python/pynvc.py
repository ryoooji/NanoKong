try:
    import pyzwave
except ImportError:
    pyzwave = 0
import pyzigbee


REPRG_OPEN                   = 0x10
REPRG_OPEN_R                 = 0x11
REPRG_WRITE                  = 0x20
REPRG_WRITE_R_OK             = 0x21
REPRG_WRITE_R_RETRANSMIT     = 0x22
REPRG_COMMIT                 = 0x30
REPRG_COMMIT_R_OK            = 0x31
REPRG_COMMIT_R_RETRANSMIT    = 0x32
REPRG_COMMIT_R_FAILED        = 0x33

GETRUNLVL                    = 0x50
GETRUNLVL_R                  = 0x51
SETRUNLVL                    = 0x60
SETRUNLVL_R                  = 0x61

APPMSG                       = 0x80
APPMSG_R                     = 0x81

#WKPF message types here
WKPF_GET_WUCLASS_LIST	       = 0x90
WKPF_GET_WUCLASS_LIST_R	     = 0x91
WKPF_GET_WUOBJECT_LIST	     = 0x92
WKPF_GET_WUOBJECT_LIST_R	   = 0x93
WKPF_READ_PROPERTY	         = 0x94
WKPF_READ_PROPERTY_R    	   = 0x95
WKPF_WRITE_PROPERTY	         = 0x96
WKPF_WRITE_PROPERTY_R	       = 0x97
WKPF_REQUEST_PROPERTY_INIT   = 0x98
WKPF_REQUEST_PROPERTY_INIT_R = 0x99

DEBUG_TRACE_PART             = 0xA0
DEBUG_TRACE_FINAL            = 0xA2


WKPF_ERROR_R        	       = 0x9F

APPMSG_STATUS_WAIT_ACK       = 0x00
APPMSG_STATUS_ACK            = 0x01
APPMSG_STATUS_BUSY           = 0x02

RUNLVL_VM                    = 0x02
RUNLVL_CONF                  = 0x03
RUNLVL_RESET                 = 0x04

pymodule = 0

def discoverNodes():
	node_lst = discover()
	gateway_id = node_lst[0]
	node_lst = node_lst[2:]
	node_lst.remove(gateway_id)
	print tuple(node_lst)
	return tuple(node_lst)
#  return (1, 3) # TODO: implement network discovery here

def sendcmd(dest, cmd, payload=[], retries=3):
  global pymodule
  pymodule.receive(10) # Clear pending messages
  while retries >= 0:
    try:
      if pymodule == pyzwave:
        pymodule.send(dest, [0x88, cmd] + payload)
      else:
        pymodule.send(dest, [cmd] + payload)
    except:
      print "=============IOError============ retries remaining:"
      print retries
      if retries <= 0:
        raise
      else:
        retries -= 1
    else:
      if cmd == APPMSG:
        src, ack = pymodule.receive(5000) # Receive ack of APPMSG, TODO: see if sending succeeded, check if src==dest
        print "APPMSG ACK:", ack
      return

def receive(waitmsec=1000):
  global pymodule
  return pymodule.receive(waitmsec)

def checkedReceive(allowedReplies, waitmsec=1000, verify=None):
  global pymodule
  while True:
    src, reply = pymodule.receive(waitmsec)
    if reply == None:
      print "No reply received. One of", allowedReplies, "expected."
      return None
    if not reply[0] in allowedReplies:
      print "Incorrect reply received. One of", allowedReplies, "expected, but got:", reply
      print "Dropped message"
    else:
      # Correct type received, possibly need to verify
      if verify==None or verify(reply[0], reply[1:]):
        return src, reply
      else:
        print "Incorrect reply received. Message type correct, but didnt pass verification:", reply
        print "Dropped message"

def sendWithRetryAndCheckedReceive(destination, command, allowedReplies, payload=[], waitmsec=1000, retries=0, quitOnFailure=False, verify=None):
  while retries >= 0:
    try:
      sendcmd(destination, command, payload)
      src, reply = checkedReceive(allowedReplies, waitmsec, verify=verify)
      if not reply == None:
        return src, reply
    except:
      pass
    retries -= 1
  if quitOnFailure:
    print "=====FAIL====="
    print "No reply received for command:"
    print command
    print "payload:"
    print payload
    print "Aborting"
    quit()
  else:
    return None, None

def init(option):
    global pymodule
    if option == 0:
        pyzwave.init("10.3.36.231")
        pymodule = pyzwave
    elif option == 1:
        pyzigbee.init()
        pymodule = pyzigbee
    pymodule.setdebug(False)

#Sen 12.8.7
#result structure (self_id, total_nodes(include self), node_1_id, node_2_id.....)
def discover():		
	global pymodule
	
	result = pyzwave.discover()
	print "discover result:"
	print "self id:"+ str(result[0])
	print "node id:",
	for i in range(2, result[1]+2):
		if result[i]!=result[0]:
			print(str(result[i])+ " "),
	print "\n",
	return result