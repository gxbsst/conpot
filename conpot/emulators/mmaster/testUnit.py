__author__ = 'tangjiashan'
import time
from opcua import ua, Client
class SubHandler(object):

    def data_change(self, handle, node, val, attr):
        print("Python: New data change event", handle, node, val, attr)


if __name__ == "__main__":
    client = Client("opc.tcp://10.9.192.199:4881/ua/server/")
    client.connect()

    root = client.get_root_node()
    # obj = root.get_child(["0:Objects", "0:MJGrooveRobot"])
    # res = obj.call_method("0:Start", 10,10)

    # obj = root.get_child(["0:Objects", "0:SSRobot"])
    # res = obj.call_method("0:MovingStart", 0,3)

    # res = obj.call_method("0:WeldingStart", 3)

    # obj = root.get_child(["0:Objects", "0:SSRobot"])
    # res = obj.call_method("0:WeldingStart", 1)

    obj = root.get_child(["0:Objects", "0:SSAgv"])
    res = obj.call_method("0:SendOrder", 1, 11, 1)

    # obj = root.get_child(["0:Objects", "0:MJMoveRobot"])
    # res = obj.call_method("0:Start", 1)
    #getting a variable by path and setting its value attribute
    # var = root.get_child(["0:Objects", "0:MJMoveRobot", "0:MagnetConfirm"])
    # print var
    # var.set_value(ua.Variant([23], ua.VariantType.Int64))

    #subscribing to data change event to our variable
    # handler = SubHandler()
    # sub = client.create_subscription(500, handler)
    # sub.subscribe_data_change(var)

    print res

    client.disconnect()