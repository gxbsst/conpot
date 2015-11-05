
import gevent.monkey
gevent.monkey.patch_all()

import unittest
from collections import namedtuple

from conpot.tests.helpers.dct_server import DCTServer
from conpot.emulators.dct.dct import DCT

import conpot.core as conpot_core
import time
import threading


class TestBase(unittest.TestCase):

    def setUp(self):
        # clean up before we start...
        conpot_core.get_sessionManager().purge_sessions()

        self.dct_server = DCTServer()
        gevent.spawn(self.dct_server.start)
        gevent.sleep(0.5)

        # self.databus = conpot_core.get_databus()
        # self.databus.initialize('conpot/templates/default/template.xml')
        args = namedtuple('FakeArgs', '')
        self.dct = DCT('conpot/templates/default/dct/dct.xml', 'none', args)

        gevent.spawn(self.dct.start, '0.0.0.0', 9002)
        gevent.sleep(0.5)

    def tearDown(self):
        self.dct.stop()
        self.dct_server.stop()

    def test_get_state(self):
        self.assertEqual(self.dct.state.value, 1)
