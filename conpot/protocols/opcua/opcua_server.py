from opcua import ua, Server
from conpot.protocols.opcua import xmlimporter
import logging

logger = logging.getLogger(__name__)


class OPCUAServer(Server):

    def __init__(self, template, template_directory, args):
        Server.__init__(self)
        importer = xmlimporter.XmlImporter(self)
        importer.import_xml(template)

    def start(self, host, port):
        self.set_endpoint("opc.tcp://" + str(host) + ":" + str(port) + "/ua/server/")
        self.set_server_name("OPCUA Server")
        logger.info('OPCUA server started on: %s', (host, port))
        Server.start(self)

    def stop(self):
        Server.stop(self)