#!/usr/bin/python
# vim: ts=2 sw=2
# author: Penn Su
from gevent import monkey; monkey.patch_all()
import tornado.ioloop
import tornado.web
import tornado.template as template
import os, sys, zipfile
import simplejson as json
import logging
import hashlib
from xml.dom.minidom import parse, parseString
from threading import Thread
import traceback
import time
import re
import StringIO
import shutil, errno
import datetime
from subprocess import Popen, PIPE, STDOUT

sys.path.append(os.path.abspath("../tools/python"))
sys.path.append(os.path.abspath("../tools/xml2java"))
import fakedata
import wusignal
from wkapplication import WuApplication
from wkpf import *
from wkpfcomm import *
from inspector import Inspector

from configuration import *

import tornado.options
tornado.options.parse_command_line()
tornado.options.enable_pretty_logging()
logging.info('now you see me, you cannot unsee')

IP = sys.argv[1] if len(sys.argv) >= 2 else '127.0.0.1'

locationTree= None

active_ind = 0
applications = []
node_infos = []
#######################
# KatsunoriSato added #
#######################
from make_js import make_main
from make_fbp import fbp_main
def import_wuXML():
	test = make_main()
	test.make()
	
def make_FBP():
	test_1 = fbp_main()
	test_1.make()	

#######################

# Helper functions
def allowed_file(filename):
  return '.' in filename and \
      filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def active_application():
  return applications[active_ind]

def copyAnything(src, dst):
  try:
    shutil.copytree(src, dst)
  except OSError as exc: # python >2.5
    if exc.errno == errno.ENOTDIR:
      shutil.copy(src, dst)
    else: raise

def getAppIndex(app_id):
  global applications
  # make sure it is not unicode
  app_id = app_id.encode('ascii','ignore')
  for index, app in enumerate(applications):
    if app.id == app_id:
      return index
  return None

def delete_application(i):
  global applications
  try:
    shutil.rmtree(applications[i].dir)
    #os.system('rm -rf ' + applications[i].dir)
    applications.pop(i)
    return True
  except Exception as e:
    print e
    print False

def load_app_from_dir(dir):
  app = WuApplication(dir=dir)
  app.loadConfig()
  return app

def update_applications():
  global applications
  print 'update applications'

  application_basenames = [os.path.basename(app.dir) for app in applications]

  for dirname in os.listdir(APP_DIR):
    app_dir = os.path.join(APP_DIR, dirname)
    print app_dir
    if dirname.lower() == 'base': continue
    if not os.path.isdir(app_dir): continue

    if dirname not in application_basenames:
      print 'not found'
      print repr(dirname)
      print repr(application_basenames)
      applications.append(load_app_from_dir(app_dir))
      application_basenames = [os.path.basename(app.dir) for app in applications]

def getPropertyValuesOfApp(mapping_results, property_names):
  print 'getPropertyValuesOfApp'
  properties_json = []

  comm = getComm()
  for wuobject in mapping_results.values():
    for name in property_names:
      if name in wuobject:
        wuproperty = wuobject.getPropertyByName(name)
        print wuobject
        print wuproperty
        (value, datatype, status) = comm.getProperty(wuobject, int(wuproperty.getId()))
        properties_json.append({'name': name, 'value': value, 'wuclassname': wuproperty.getWuClassName()})

  return properties_json

# List all uploaded applications
class main(tornado.web.RequestHandler):
  def get(self):
    self.render('templates/application.html')

class list_applications(tornado.web.RequestHandler):
  def get(self):
    self.render('templates/index.html', applications=applications)

  def post(self):
    global applications
    update_applications()
    apps = [application.config() for application in applications]
    self.content_type = 'application/json'
    self.write(json.dumps(apps))

  '''
  def post(self):
    global applications

    if not self.get_argument('name') or not self.request.files['bog_file']:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'name or bog file is missing, please fill in the information'})
    else:
      received = self.request.files['bog_file'][0]
      file = StringIO.StringIO()
      file.write(received['body'])
      filename = received['filename']

      if file and allowed_file(filename):
        applications.append(WuApplication(self.get_argument('name'), self.get_argument('desc'), self.factory, file))
        self.content_type = 'application/json'
        self.write({'status':0, 'id':len(applications)-1})
      else:
        self.content_type = 'application/json'
        self.write({'status':1})
  '''

# Returns a form to upload new application
class new_application(tornado.web.RequestHandler):
  def post(self):
    global applications
    #self.redirect('/applications/'+str(applications[-1].id), permanent=True)
    #self.render('templates/upload.html')
    try:
      app_name = 'application' + str(len(applications))
      app_id = hashlib.md5(app_name).hexdigest()

      # copy base for the new application
      print 'setting up app directory from base...'
      copyAnything(BASE_DIR, os.path.join(APP_DIR, app_id))

      app = WuApplication(id=app_id, name=app_name, dir=os.path.join(APP_DIR, app_id))
      applications.append(app)

      print app

      # dump config file to app
      app.saveConfig()

      self.content_type = 'application/json'
      self.write({'status':0, 'app': app.config()})
    except Exception as e:
      print e
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg':'Cannot create application'})

class application(tornado.web.RequestHandler):
  # topbar info
  def get(self, app_id):
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      title = ""
      if self.get_argument('title'):
        title = self.get_argument('title')
      app = applications[app_ind].config()
      topbar = template.Loader(os.getcwd()).load('templates/topbar.html').generate(application=applications[app_ind], title=title)
      self.content_type = 'application/json'
      self.write({'status':0, 'app': app, 'topbar': topbar})

  # Display a specific application
  def post(self, app_id):
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      app = applications[app_ind].config()
      #app = {'name': applications[app_ind].name, 'desc': applications[app_ind].desc, 'id': applications[app_ind].id}
      topbar = template.Loader(os.getcwd()).load('templates/topbar.html').generate(application=applications[app_ind], title="Flow Based Programming")
      self.content_type = 'application/json'
      self.write({'status':0, 'app': app, 'topbar': topbar})

  # Update a specific application
  def put(self, app_id):
    global applications
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      print 'save_application'
      try:
        applications[app_ind].name = self.get_argument('name', 'application name')
        applications[app_ind].desc = self.get_argument('desc', '')
        applications[app_ind].saveConfig()
        self.content_type = 'application/json'
        self.write({'status':0})
      except Exception as e:
        print e
        self.content_type = 'application/json'
        self.write({'status':1, 'mesg': 'Cannot save application'})

  # Destroy a specific application
  def delete(self, app_id):
    global applications
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      print 'delete_application'
      if delete_application(app_ind):
        self.content_type = 'application/json'
        self.write({'status':0})
      else:
        self.content_type = 'application/json'
        self.write({'status':1, 'mesg': 'Cannot delete application'})

class deploy_application(tornado.web.RequestHandler):
  def get(self, app_id):
    global applications
    global node_infos
    try:
      # Discovery results
      # TODO: persistent store
      #comm = getComm()
      #node_infos = comm.getAllNodeInfos()

      

      app_ind = getAppIndex(app_id)
      if app_ind == None:
        self.content_type = 'application/json'
        self.write({'status':1, 'mesg': 'Cannot find the application'})
      else:
        deployment = template.Loader(os.getcwd()).load('templates/deployment.html').generate(app=applications[app_ind], app_id=app_id, node_infos=node_infos, logs=applications[app_ind].logs(), mapping_results=applications[app_ind].mapping_results, set_location=False)
        self.content_type = 'application/json'
        self.write({'status':0, 'page': deployment})

    except Exception as e:
      print e
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot initiate connection with the baseStation'})

  def post(self, app_id):
    global applications
    global node_infos
    global active_ind
    node_ids = [info.nodeId for info in node_infos]
    app_ind = getAppIndex(app_id)
    # Discovery results
    # TODO: persistent store
      
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      platforms = ['avr_mega2560']
      # TODO: need platforms from fbp

      if len(node_ids) > 0 and applications[app_ind].deploy(node_ids, platforms):
        active_ind = app_ind
        self.content_type = 'application/json'
        self.write({'status':0, 'version': applications[app_ind].version})
      else:
        self.content_type = 'application/json'
        self.write({'status':1, 'mesg': 'Deploy has failed'})
 #   else:   
      #in simulation, we should also deploy the sensor nodes into the simulation nodes
      #TODO: implement the deployment part
  #    self.content_type = 'application/json'
   #   self.write({'status':1, 'version': applications[app_ind].version})

class map_application(tornado.web.RequestHandler):
  def post(self, app_id):
    global applications
    global locationTree
    global node_infos

    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      platforms = ['avr_mega2560']
      # TODO: need platforms from fbp

#      comm.addActiveNodesToLocTree(fakedata.locTree)
      locationTree.printTree(locationTree.root)

      # Map with location tree info (discovery), this will produce mapping_results
      applications[app_ind].map(locationTree)

     # print '[][][][]mapping results'
    #  print applications[app_ind].mapping_results

      ret = []
      for key, value in applications[app_ind].mapping_results.items():
        for ind, wuobj in enumerate(value):
          if ind == 0:
            ret.append({'leader': True, 'instanceId': wuobj.getInstanceId(), 'name': wuobj.getWuClassName(), 'nodeId': wuobj.getNodeId(), 'portNumber': wuobj.getPortNumber()})
          else:
            ret.append({'leader': False, 'instanceId': wuobj.getInstanceId(), 'name': wuobj.getWuClassName(), 'nodeId': wuobj.getNodeId(), 'portNumber': wuobj.getPortNumber()})

      print ret

      self.content_type = 'application/json'
      self.write({'status':0, 'mapping_results': ret, 'version': applications[app_ind].version})

class monitor_application(tornado.web.RequestHandler):
  def get(self, app_id):
    global applications
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    #elif not applications[app_ind].mapping_results or not applications[app_ind].deployed:
      #self.content_type = 'application/json'
      #self.wrtie({'status':1, 'mesg': 'No mapping results or application out of sync, please deploy the application first.'})
    else:
      #applications[app_ind].inspector = Inspector(applications[app_ind].mapping_results)

      #properties_json = {}
      properties_json = getPropertyValuesOfApp(applications[app_ind].mapping_results, [property.getName() for wuobject in applications[app_ind].mapping_results.values() for property in wuobject])
      print properties_json

      monitor = template.Loader(os.getcwd()).load('templates/monitor.html').generate(app=applications[app_ind], mapping_results={}, logs=applications[app_ind].logs(), properties_json=properties_json)
      self.content_type = 'application/json'
      self.write({'status':0, 'page': monitor})

class properties_application(tornado.web.RequestHandler):
  def post(self, app_id):
    global applications
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      properties_json = getPropertyValuesOfApp(applications[app_ind].mapping_results, [property.getName() for wuobject in applications[app_ind].mapping_results.values() for property in wuobject])
      print properties_json

      self.content_type = 'application/json'
      self.write({'status':0, 'properties': properties_json})

# Never let go
class poll(tornado.web.RequestHandler):
  def post(self, app_id):
    global applications
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      #print applications[app_ind].version, self.get_argument('version')
      #if int(applications[app_ind].version) <= int(self.get_argument('version')):
        #self.content_type = 'application/json'
        #self.write({'status':0, 'version': applications[app_ind].version, 'returnCode': applications[app_ind].returnCode, 'logs': applications[app_ind].retrieve()})
      #else:
      self.content_type = 'application/json'
      self.write({'status':0, 'version': applications[app_ind].version, 'returnCode': applications[app_ind].returnCode, 'logs': applications[app_ind].retrieve()})

class save_fbp(tornado.web.RequestHandler):
  def post(self, app_id):
    global applications
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      xml = self.get_argument('xml')
      applications[app_ind].updateXML(xml)
      applications[app_ind] = load_app_from_dir(applications[app_ind].dir)
      applications[app_ind].xml = xml
      applications[app_ind].setFlowDom(parseString(xml))
      # TODO: need platforms from fbp
      #platforms = self.get_argument('platforms')
      platforms = ['avr_mega2560']

      self.content_type = 'application/json'
      self.write({'status':0, 'version': applications[app_ind].version})

class load_fbp(tornado.web.RequestHandler):
  def get(self, app_id):
    self.render('templates/fbp.html')

  def post(self, app_id):
    global applications
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      self.content_type = 'application/json'
      self.write({'status':0, 'xml': applications[app_ind].xml})

class poll_testrtt(tornado.web.RequestHandler):
  def post(self):
    global applications
    if SIMULATION == 0:
      comm = getComm()
      status = comm.currentStatus()
      if status != None:
        self.content_type = 'application/json'
        self.write({'status':0, 'logs': status.split('\n')})
      else:
        self.content_type = 'application/json'
        self.write({'status':0, 'logs': []})
    else:
      self.content_type = 'application/json'
      self.write({'status':0, 'logs': []})

class stop_testrtt(tornado.web.RequestHandler):
  def post(self):
    global applications
    if SIMULATION == 0:
      comm = getComm()
      if comm.onStopMode():
        self.content_type = 'application/json'
        self.write({'status':0})
      else:
        self.content_type = 'application/json'
        self.write({'status':1})
    else:
      self.content_type = 'application/json'
      self.write({'status':2})

class exclude_testrtt(tornado.web.RequestHandler):
  def post(self):
    global applications
    if SIMULATION == 0:
      comm = getComm()
      if comm.onDeleteMode():
        self.content_type = 'application/json'
        self.write({'status':0, 'log': 'Going into exclude mode'})
      else:
        self.content_type = 'application/json'
        self.write({'status':1, 'log': 'There is an error going into exclude mode'})
    else:    
      self.content_type = 'application/json'
      self.write({'status':2, 'log': 'Not available in simulation'})

class include_testrtt(tornado.web.RequestHandler):
  def post(self):
    global applications
    if SIMULATION == 0:
      comm = getComm()
      print 'onAddMode'
      if comm.onAddMode():
        self.content_type = 'application/json'
        self.write({'status':0, 'log': 'Going into include mode'})
      else:
        self.content_type = 'application/json'
        self.write({'status':1, 'log': 'There is an error going into include mode'})
    else:
      self.content_type = 'application/json'
      self.write({'status':2, 'log': 'Not available in simulation'})

class testrtt(tornado.web.RequestHandler):
  def get(self):

    global node_infos
    if SIMULATION == 0:
        comm = getComm()
        node_infos = comm.getAllNodeInfos()
    elif SIMULATION == 1:
        node_infos = fakedata.simNodeInfos
    else:
        logging.info("SIMULATION set to invalid value")

    # debug purpose
    #node_infos = fakedata.node_infos

    testrtt = template.Loader(os.getcwd()).load('templates/testrtt.html').generate(log=['Please press the buttons to add/remove nodes.'], node_infos=node_infos, set_location=True)
    self.content_type = 'application/json'
    self.write({'status':0, 'testrtt':testrtt})

class refresh_nodes(tornado.web.RequestHandler):
  def post(self):
    global node_infos
    if SIMULATION == 0:
      print 'refresh_nodes'
      comm = getComm()
      print 'after getComm()'
      node_infos = comm.getAllNodeInfos(force=True)
    elif SIMULATION ==1:
      print ('using simulation data 1')
      node_infos = fakedata.simNodeInfos
    else:
      logging.info("SIMULATION set to invalid value"+ str(SIMULATION))
    for info in node_infos:
      senNd = SensorNode(info, 0, 0, 0)
      locationTree.addSensor(senNd)
    locationTree.printTree()
    # default is false
    set_location = self.get_argument('set_location', False)

    nodes = template.Loader(os.getcwd()).load('templates/monitor-nodes.html').generate(node_infos=node_infos, set_location=set_location)

    self.content_type = 'application/json'
    self.write({'status':0, 'nodes': nodes})

class nodes(tornado.web.RequestHandler):
  def get(self):
    pass

  def post(self, nodeId):
    info = None
    if SIMULATION == 0:
      comm = getComm()
      info = comm.getNodeInfo(nodeId)
    elif SIMULATION == 1:
      for i in range(fakedata.simNodeInfos):
          if fakedata.simNodeInfos[i].nodeId == nodeId:
              info = fakedata.simNodeInfos[i]
    else:
        logging.info("SIMULATION set to invalid value")
        exit()
              

    self.content_type = 'application/json'
    self.write({'status':0, 'node_info': info})

  def put(self, nodeId):
    global locationTree
    global node_infos
    location = self.get_argument('location')
    if location:
      comm = getComm()
      if comm.setLocation(int(nodeId), location):
        # update our knowledge too
        for info in comm.all_node_infos:
          if info.nodeId == int(nodeId):
            info.location = location
            senNd = SensorNode(info, 0, 0, 0)
            locationTree.addSensor(senNd)
        locationTree.printTree()
        self.content_type = 'application/json'
        self.write({'status':0})
      else:
        self.content_type = 'application/json'
        self.write({'status':1, 'mesg': 'Cannot set location, please try again.'})
        
class tree(tornado.web.RequestHandler):	
#	def get(self):
#		pass
		
	def post(self):
		global locationTree
		global node_infos
		
		locationTree.reset(LOCATION_ROOT)	
		if SIMULATION == 0:
			comm = getComm()
			node_infos = comm.getAllNodeInfos()
		elif SIMULATION == 1:
			node_infos = fakedata.simNodeInfos
		else:
			logging.info("SIMULATION set to invalid value")

		for info in node_infos:
			senNd = SensorNode(info, 0, 0, 0)
			locationTree.addSensor(senNd)

		addloc = template.Loader(os.getcwd()).load('templates/display_locationTree.html').generate(node_infos=node_infos)

		locationTree.printTree()
		disploc = locationTree.getJson()
		self.content_type = 'application/json'
		self.write({'loc':json.dumps(disploc),'node':addloc})			

       
settings = dict(
  static_path=os.path.join(os.path.dirname(__file__), "static"),
  debug=True
)

app = tornado.web.Application([
  (r"/", main),
  (r"/main", main),
  (r"/testrtt/exclude", exclude_testrtt),
  (r"/testrtt/include", include_testrtt),
  (r"/testrtt/stop", stop_testrtt),
  (r"/testrtt/poll", poll_testrtt),
  (r"/testrtt", testrtt),
  (r"/nodes/([1-9]*)", nodes),
  (r"/nodes/refresh", refresh_nodes),
  (r"/applications", list_applications),
  (r"/applications/new", new_application),
  (r"/applications/([a-fA-F\d]{32})", application),
  (r"/applications/([a-fA-F\d]{32})/properties", properties_application),
  (r"/applications/([a-fA-F\d]{32})/poll", poll),
  (r"/applications/([a-fA-F\d]{32})/deploy", deploy_application),
  (r"/applications/([a-fA-F\d]{32})/deploy/map", map_application),
  (r"/applications/([a-fA-F\d]{32})/monitor", monitor_application),
  (r"/applications/([a-fA-F\d]{32})/fbp/save", save_fbp),
  (r"/applications/([a-fA-F\d]{32})/fbp/load", load_fbp),
  (r"/test/tree", tree)
], IP, **settings)

ioloop = tornado.ioloop.IOLoop.instance()
if __name__ == "__main__":
  update_applications()
  tornado.ioloop.PeriodicCallback(wusignal.signal_handler, 100, ioloop)
  app.listen(MASTER_PORT)
  locationTree = LocationTree(LOCATION_ROOT)
  import_wuXML()	#KatsunoriSato added
  make_FBP()
  ioloop.start()

