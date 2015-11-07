# coding=utf-8

from opcua import ua, Server
from lxml import etree
import logging
import conpot.core as conpot_core

logger = logging.getLogger(__name__)


class SubHandler(object):
    """
    Subscription Handler. To receive events from server for a subscription
    """

    def data_change(self, handle, node, val, attr):
        conpot_core.get_databus().set_value('w ' + node.nodeid.to_string(), val)

    def event(self, handle, event):
        pass


class OPCUAServer(Server):
    def __init__(self, template, template_directory, args):
        Server.__init__(self)
        dom = etree.parse(template)

        # Server name
        root = dom.xpath('//opcua')[0]
        self.set_server_name(root.attrib['name'])

        # Folders
        folders = dom.xpath('//opcua/folder')
        for folder in folders:
            parent = self.get_objects_node()
            for attr, value in folder.items():
                if attr == 'parent':
                    parent_id = folder.root['parent']
                    parent = self.get_node(parent_id)
                    break
            parent.add_folder(folder.attrib['node_id'], folder.attrib['browser_name'])

        self.variables = []

        # Objects
        objects = dom.xpath('//opcua/object')
        for obj in objects:
            parent = self.get_objects_node()
            for attr, value in obj.items():
                if attr == 'parent':
                    parent_id = obj.attrib['parent']
                    parent = self.get_node(parent_id)
                    break
            ua_object = parent.add_folder(obj.attrib['node_id'], obj.attrib['browser_name'])
            variables = obj.xpath('./variable')
            for variable in variables:
                value = variable.xpath('./value')[0]
                node_id = variable.attrib['node_id']
                ua_variable = ua_object.add_variable(variable.attrib['node_id'],
                                                     variable.attrib['browser_name'],
                                                     eval(value.attrib['type'] + "('" + value.text + "')"))
                self.variables.append(ua_variable)
                conpot_core.get_databus().observe_value('r ' + node_id,
                                                        lambda key: self.get_node(key[2:]).set_value(
                                                            conpot_core.get_databus().get_value(key)))

    def start(self, host, port):
        self.set_endpoint("opc.tcp://" + str(host) + ":" + str(port) + "/ua/server/")
        logger.info('OPCUA server started on: %s', (host, port))
        Server.start(self)

        # Subscription Handler
        handler = SubHandler()
        sub = self.create_subscription(500, handler)
        for ua_variable in self.variables:
            sub.subscribe_data_change(ua_variable)

    def stop(self):
        Server.stop(self)