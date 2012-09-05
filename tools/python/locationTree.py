#the children of leaf nodes are sensor nodes, sensor nodes
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../python"))
from wkpf import NodeInfo, WuClass, WuObject

class SensorNode(object):
    def __init__(self, locationLst, nodeInfo, x_coord, y_coord, z_coord):
        self.locationLst = locationLst
        self.nodeInfo = nodeInfo
        self.coord = (x_coord,y_coord,z_coord)
        self.port_list = []

    def initPortList(self, forceInit = True):
        if len(self.port_list)!=0 and forceInit == False:
            return
        for wuObj in self.nodeInfo.wuObjects:
            self.port_list.append(wuObj.portNumber)
        self.port_list.sort()

    def reserveNextPort(self):
        portSet = False
        for j in range(len(self.port_list)):
            if (self.port_list[j]+1)%256 !=self.port_list[(j+1)%len(self.port_list)]:
                self.port_list.append((self.port_list[j]+1)%256)
                self.port_list.sort()
                portSet =True
                return (self.port_list[j]+1)%256
        return None

class LocationTreeNode(object):
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.children = []
        self.childrenCnt = 0
        self.sensorLst = []
        self.sensorCnt = 0
        self.idSet = set()

    def addChild(self, name):
        tmp = LocationTreeNode (name, self)
        self.children.append(tmp)
        self.childrenCnt = self.childrenCnt + 1
        return self.children[-1]

    def addSensor(self, sensorNode):
        self.sensorLst.append(sensorNode)
        self.sensorCnt = self.sensorCnt + 1
        self.idSet.add(sensorNode.nodeInfo.nodeId)

    def getAllNodes(self):
        ret_val = self.idSet
        for child in self.children:
            ret_val = ret_val | child.getAllNodes()
        return ret_val

    def printTreeNode(self, indent):
        print_str = ""
        for i in range(indent):
            print_str  = print_str + "\t"
        print_str = print_str + self.name + "#"
        for i in range(self.sensorCnt):
            print_str = print_str + str(self.sensorLst[i].nodeInfo.nodeId) +str(self.sensorLst[i].coord)+", "
        print(print_str)

# Sorry, no multiple constructors in Python
# http://stackoverflow.com/questions/682504/what-is-a-clean-pythonic-way-to-have-multiple-constructors-in-python
class LocationTree(object):
    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            self.sensor_dict = {}
            self.root = LocationTreeNode(args[0], None)
            self.totalSensorCount = 0
        elif 'name' in kwargs:
            self.sensor_dict = {}
            self.root = LocationTreeNode(kwargs['name'], None)
            self.totalSensorCount = 0

    # matched by the highest segment of location string from sensorNd, then add sensor as a LocationTreeNode to LocationTree at the last segment of the location string
    def addSensor(self, sensorNd):
        curPos = None
        if self.root.name == sensorNd.locationLst[0]:
            curPos = self.root
        else:
            for child in self.root.children:
                if child.name == sensorNd.locationLst[0]:
                    curPos = child
                    break

        if curPos == None:
            print("error! location: " + str(sensorNd.locationLst[0]) + " is not a valid value")
            return

        for locationString in sensorNd.locationLst[1:]:
            child_index = -1
            for j in range(curPos.childrenCnt):
                if curPos.children[j].name == locationString:
                    child_index = j
                    break
            if (child_index != -1):
                curPos = curPos.children[child_index]
            else:
                curPos = curPos.addChild(locationString)

        curPos.addSensor(sensorNd)
        self.sensor_dict[sensorNd.nodeInfo.nodeId] = sensorNd
        self.totalSensorCount = self.totalSensorCount +1

    '''
    #insert sensorNd into the tree with its location specified in locationLst, starting from startPos node(set to root if locationLst start from beginning)
    def addSensor(self, startPos, sensorNd):
        if startPos.name != sensorNd.locationLst[0]:
            print("error! location: "+ str(sensorNd.locationLst[0])+ " is not a valid value")
            return
        curPos = startPos
        for i in range(1, len(sensorNd.locationLst)):

            if  curPos.childrenCnt==0:
                curPos.addChild(sensorNd.locationLst[i])
                curPos = curPos.children[-1]
            else:
                child_index = -1
                for j in range(curPos.childrenCnt):
                    if curPos.children[j].name == sensorNd.locationLst[i]:
                        child_index = j
                if (child_index >= 0):
                    curPos = curPos.children[child_index]
                else:
                    curPos.addChild(sensorNd.locationLst[i])
                    curPos = curPos.children[-1]

        curPos.addSensor(sensorNd)
        self.sensor_dict[sensorNd.nodeInfo.nodeId] = sensorNd
        self.totalSensorCount = self.totalSensorCount +1
    '''

    def findLocation(self, startPos, locationStr):
        locationLst =  parseLocation(locationStr)
        if startPos.name != locationLst[0]:
            print("error! location: "+ str(sensorNd.locationLst[0])+ " is not a valid value")
            return None
        curPos = startPos
        for i in range(1, len(locationLst)):
            if  curPos.childrenCnt==0:
                return None
            else:
                child_index = -1
                for j in range(curPos.childrenCnt):
                    if curPos.children[j].name == locationLst[i]:
                        child_index = j
                if (child_index >= 0):
                    curPos = curPos.children[child_index]
                else:
                    curPos = curPos.children[-1]
        return curPos

    def printTree(self, indent = 0):
        self.printTreeNode(self.root, indent)
        for child in self.root.children:
            self.printTree(child, indent+1)


def parseLocation (locationStr):
    return locationStr.split('/')



if __name__ == "__main__":
    locTree = LocationTree("Boli_Building")
    loc0 = "Boli_Building/3F/South_Corridor"
    loc1 = "Boli_Building/3F/South_Corridor/Room318"
    loc2 = "Boli_Building/3F/East_Corridor/Room318"
    loc3 = "Boli_Building/3F/East_Corridor/Room318"
    senNd0 = SensorNode(parseLocation(loc0), NodeInfo(0,[], []), 0, 1, 2)
    senNd1 = SensorNode(parseLocation(loc1), NodeInfo(1, [], []), 0, 5, 3)
    senNd2 = SensorNode(parseLocation(loc2), NodeInfo(2, [], []), 3, 3, 2)
    senNd3 = SensorNode(parseLocation(loc3), NodeInfo(3, [], []), 2, 1, 2)
    locTree.addSensor(senNd0)
    locTree.addSensor(senNd1)
    locTree.addSensor(senNd2)
    locTree.addSensor(senNd3)
    locTree.printTree(0)

