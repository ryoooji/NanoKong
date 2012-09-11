from wkpf import *
from locationTree import *

rootpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
all_wuclasses = parseXML(os.path.join(rootpath, "ComponentDefinitions", "WuKongStandardLibrary.xml")).values()
all_wutypes = parseXML(os.path.join(rootpath, "ComponentDefinitions", "WuKongStandardLibrary.xml"), type='wutype').values()

node_infos = [NodeInfo(nodeId=3,
                wuClasses=all_wuclasses,
                wuObjects=[])]

locTree = LocationTree("Boli_Building")
'''
locs = ["Boli_Building/3F/South_Corridor/Room336", "Boli_Building/3F/East_Corridor/Room318"]
coords = [(0, 1, 2), (0, 5, 3)]

for node_info, loc, coord in zip(node_infos, locs, coords):
    locTree.addSensor(SensorNode(node_info, coord[0], coord[1], coord[2]))

queries = ["Boli_Building/3F/South_Corridor/Room318#near(0,1,2,1)|near(1,1,3,1)",
          "Boli_Building/3F/South_Corridor/Room336#near(0,1,2,1)|near(1,1,3,1)",
          None, None]
'''
