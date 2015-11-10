# coding=utf-8

from opcua import ua, Server
from opcua.node import Node
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
        self.template = template
        self.variables = []
        self.event_dict = {}

    def parse(self):
        dom = etree.parse(self.template)

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

            # Variables
            variables = obj.xpath('./variable')
            for variable in variables:
                value = variable.xpath('./value')[0]
                node_id = variable.attrib['node_id']
                ua_variable = ua_object.add_variable(variable.attrib['node_id'],
                                                     variable.attrib['browser_name'],
                                                     eval(value.attrib['type'] + "('" + value.text + "')"))
                ua_variable.set_writable(True)
                self.variables.append(ua_variable)
                conpot_core.get_databus().observe_value('r ' + node_id,
                                                        lambda key: self.get_node(key[2:]).set_value(
                                                            conpot_core.get_databus().get_value(key)))

            # Methods
            methods = obj.xpath('./method')
            for method in methods:
                method_node_id = method.attrib['node_id']
                method_browser_name = method.attrib['browser_name']

                input_args = method.xpath('./input_args')
                ua_input_args = []
                if input_args is not None and len(input_args) > 0:
                    for arg in input_args[0].text.split(',', 1):
                        ua_input_args.append(ua.VariantType[arg])

                output_args = method.xpath('./output_args')
                ua_output_args = []
                for arg in output_args[0].text.split(',', 1):
                    ua_output_args.append(ua.VariantType[arg])

                exec method.xpath('./func')[0].text.strip() in {
                    'Server': OPCUAServer,
                    'server': self,
                    'ua': ua,
                    'databus': conpot_core.get_databus(),
                    'ua_object': ua_object,
                    'node_id': method_node_id,
                    'browser_name': method_browser_name,
                    'input_args': ua_input_args,
                    'output_args': ua_output_args
                }

            # Events
            events = obj.xpath('./event')
            for event in events:
                event_id = event.attrib['event_id']
                severity = int(event.attrib['severity'])
                message_text = event.xpath('./message')[0].text

                ua_event = self.get_event_object(ua.ObjectIds.BaseEventType)
                ua_event.EventId = event_id
                ua_event.Message.Text = message_text
                ua_event.Severity = severity
                self.event_dict[event_id] = ua_event

                conpot_core.get_databus().observe_value('r ' + event_id,
                                                        lambda key: self.event_dict[key[2:]].trigger())

    def start(self, host, port):
        # 首先解析XML
        self.parse()

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

    @staticmethod
    def create_method(parent, *args):
        nodeid, qname = OPCUAServer._parse_add_args(*args[:2])
        callback = args[2]
        if len(args) > 3:
            inputs = args[3]
        if len(args) > 4:
            outputs = args[4]
        return OPCUAServer._create_method(parent, nodeid, qname, callback, inputs, outputs)

    @staticmethod
    def _parse_add_args(*args):
        if isinstance(args[0], ua.NodeId):
            return args[0], args[1]
        elif isinstance(args[0], str):
            return ua.NodeId.from_string(args[0]), ua.QualifiedName.from_string(args[1])
        elif isinstance(args[0], int):
            return ua.generate_nodeid(args[0]), ua.QualifiedName(args[1], args[0])
        else:
            raise TypeError("Add methods takes a nodeid and a qualifiedname as argument, received %s" % args)

    @staticmethod
    def _create_method(parent, nodeid, qname, callback, inputs, outputs):
        node = ua.AddNodesItem()
        node.RequestedNewNodeId = nodeid
        node.BrowseName = qname
        node.NodeClass = ua.NodeClass.Method
        node.ParentNodeId = parent.nodeid
        node.ReferenceTypeId = ua.NodeId.from_string("i=47")
        attrs = ua.MethodAttributes()
        attrs.Description = ua.LocalizedText(qname.Name)
        attrs.DisplayName = ua.LocalizedText(qname.Name)
        attrs.WriteMask = ua.OpenFileMode.Read
        attrs.UserWriteMask = ua.OpenFileMode.Read
        attrs.Executable = True
        attrs.UserExecutable = True
        node.NodeAttributes = attrs
        results = parent.server.add_nodes([node])
        results[0].StatusCode.check()
        method = Node(parent.server, nodeid)
        if inputs:
            method.add_property(ua.NodeId.from_string(method.nodeid.to_string() + '.InputArguments'),
                                ua.QualifiedName("InputArguments", 0),
                                [OPCUAServer._vtype_to_argument(vtype) for vtype in inputs])
        if outputs:
            method.add_property(ua.NodeId.from_string(method.nodeid.to_string() + '.OutputArguments'),
                                ua.QualifiedName("OutputArguments", 0),
                                [OPCUAServer._vtype_to_argument(vtype) for vtype in outputs])
        parent.server.add_method_callback(method.nodeid, callback)
        return nodeid

    @staticmethod
    def _vtype_to_argument(vtype):
        if isinstance(vtype, ua.Argument):
            return ua.ExtensionObject.from_object(vtype)

        arg = ua.Argument()
        v = ua.Variant(None, vtype)
        arg.DataType = OPCUAServer._guess_uatype(v)
        return ua.ExtensionObject.from_object(arg)

    @staticmethod
    def _guess_uatype(variant):
        if variant.VariantType == ua.VariantType.ExtensionObject:
            if variant.Value is None:
                raise Exception("Cannot guess DataType from Null ExtensionObject")
            if type(variant.Value) in (list, tuple):
                if len(variant.Value) == 0:
                    raise Exception("Cannot guess DataType from Null ExtensionObject")
                extobj = variant.Value[0]
            else:
                extobj = variant.Value
            objectidname = ua.ObjectIdsInv[extobj.TypeId.Identifier]
            classname = objectidname.split("_")[0]
            return ua.NodeId(getattr(ua.ObjectIds, classname))
        else:
            return ua.NodeId(getattr(ua.ObjectIds, variant.VariantType.name))