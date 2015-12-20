__author__ = 'tangjiashan'
import time
from opcua import ua, Client
class SubHandler(object):
    def data_change(self, handle, node, val, attr):
        print("Python: New data change event", handle, node, val, attr)


if __name__ == "__main__":
    # client = Client("opc.tcp://localhost:4881/ua/server/")
    client = Client("opc.tcp://10.9.192.199:4881/ua/server/", timeout=10)
    client.connect()

    root = client.get_root_node()

    # obj = root.get_child(["0:Objects", "0:SSRobot"])
    # res = obj.call_method("0:MovingStart", 2, 1)


    # obj = root.get_child(["0:Objects", "0:SSRobot"])
    # res = obj.call_method("0:WeldingStart", 2)

    # obj = root.get_child(["0:Objects", "0:MJGrooveRobot"])
    # res = obj.call_method("0:Start", 2, 2)

    # obj = root.get_child(["0:Objects", "0:MJMoveRobot"])
    # res = obj.call_method("0:Start", 1)

    obj = root.get_child(["0:Objects", "0:SSAgv"])
    res = obj.call_method("0:SendOrder", 4, 10, 1)


    # obj = root.get_child(["0:Objects", "0:MJWarehouse"])
    # res = obj.call_method("0:Start", 1, 1, 2)
    #
    #
    # obj = root.get_child(["0:Objects", "0:KYRgv"])
    # res = obj.call_method("0:Go", 1, 2)
    print res

    client.disconnect()