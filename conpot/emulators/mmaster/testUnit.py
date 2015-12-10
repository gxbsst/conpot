__author__ = 'tangjiashan'
import time
from opcua import ua, Client
class SubHandler(object):

    def data_change(self, handle, node, val, attr):
        print("Python: New data change event", handle, node, val, attr)


if __name__ == "__main__":
    client = Client("opc.tcp://localhost:4881/ua/server/")
    client.connect()

    root = client.get_root_node()

    #obj = root.get_child(["0:Objects", "0:SSRobot"])
    #res = obj.call_method("0:MovingStart", 0,0)

    #res = obj.call_method("0:WeldingStart", 3)

    obj = root.get_child(["0:Objects", "0:SSRobot"])
    res = obj.call_method("0:WeldingStart", 1)

    #obj = root.get_child(["0:Objects", "0:SSAgv"])
    #res = obj.call_method("0:SendOrder", 1, 5, 9)

    #obj = root.get_child(["0:Objects", "0:MJWarehouse"])
    #res = obj.call_method("0:Start", 1, 4, 1)
    print res

    client.disconnect()