# coding=utf-8

import gevent
import sys
import time

# ---------------------------------------------------------------------------#
# configure the server logging
# ---------------------------------------------------------------------------#
import logging
import fanuc_robot_parser, http_wrapper
import conpot.core as conpot_core

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

robot_parser = fanuc_robot_parser.RobotoPositionParser()


def get_html_dummy():
    answer = ""
    with open("/Users/liumin/FANUC - FANUC Robotics.htm", 'r') as f:
        answer = f.read()
    return answer


def grab():
    while True:
        html_doc = get_html_dummy()
        lines = html_doc.split('\n')
        '''
        PARSE HTML CONTENT
        If success, then return
        {   1: [<JOINT1>, <JOINT2>, <JOINT3>, <JOINT4>, <JOINT5>, <JOINT6>, <EXTAXS>],
            2: [<JOINT1>, <JOINT1>],
            3: [<JOINT1>, <JOINT1>]
        }
        '''
        try:
            result = robot_parser.parse(lines)
            conpot_core.get_databus().set_value("ns=1;s=FanucRobot.Group1Joint1", result[1][0])
        except Exception as e:
            log.error('Error grab because: %s', e.message, e)

        time.sleep(1)

def on_unhandled_greenlet_exception(dead_greenlet):
    log.error('Stopping because %s died: %s', dead_greenlet, dead_greenlet.exception)
    sys.exit(1)


greenlet = gevent.spawn(grab)
greenlet.link_exception(on_unhandled_greenlet_exception)
