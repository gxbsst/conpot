# -*- coding:utf-8 -*-
# Copyright (C) 2014 Johnny Vestergaard <jkv@unixcluster.dk>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import logging
import json
import inspect
# this is needed because we use it in the xml.
import random
import time

import gevent
import gevent.event
from lxml import etree
from influxdb import InfluxDBClient


logger = logging.getLogger(__name__)


class Databus(object):
    def __init__(self):
        self._data = {}
        self._future = {}
        self._observer_map = {}
        self.client = None
        self.initialized = gevent.event.Event()

    # the idea here is that we can store both values and functions in the key value store
    # functions could be used if a profile wants to simulate a sensor, or the function
    # could interface with a real sensor
    def get_value(self, key):
        logger.debug('DataBus: Get value from key: [%s]', key)
        real_key = key
        if key.startswith('w ') or key.startswith('r '):
            real_key = key[2:]
        assert real_key in self._data
        item = self._data[real_key]
        if getattr(item, "get_value", None):
            # this could potentially generate a context switch, but as long the called method
            # does not "callback" the databus we should be fine
            return item.get_value()
        elif hasattr(item, '__call__'):
            return item()
        else:
            # guaranteed to not generate context switch
            return item

    @staticmethod
    def get_real_key(key):
        real_key = key
        if key.startswith('w ') or key.startswith('r '):
            real_key = key[2:]
        return real_key

    def set_value(self, key, value, index=-1, sync=False, forced=False, delay=0):
        """
        放入key相关的值，并通知调用者
        当sync为True的时候将会通知调用者，并等待调用结果返回
        """
        if value is None:
            return
        logger.debug('DataBus: Storing key: [%s] value: [%s]', key, value)
        real_key = Databus.get_real_key(key)
        if forced or (real_key not in self._data or not self._data[real_key] == value):
            # store value
            if index < 0:
                self._data[real_key] = value
            else:
                data_value = self._data[real_key]
                # 如果数组长度不够直接返回
                if len(data_value) <= index:
                    return
                old_value = data_value[index]
                # 如何不是强制的,并且数组中对应的值和现在的值相等直接返回
                if not forced and old_value == value:
                    return
                data_value[index] = value
                self._data[real_key] = data_value
            # history data
            if not (real_key == 'ns=1;s=Flowmeter.Values'):
                value_field = value
                if isinstance(value, list):
                    if len(value) == 1:
                        value_field = value[0]
                json_body = [
                    {
                        "measurement": real_key,
                        "fields": {
                            "value": str(value_field)
                        }
                    }
                ]
                if self.client:
                    gevent.spawn(self.client.write_points, json_body)
            # notify observers
            if key in self._observer_map:
                if sync:
                    return self.notify_observers(key, value, sync=sync)
                gevent.spawn(self.notify_observers, key, value, delay=delay)

    def notify_observers(self, key, value, sync=False, delay=0):
        if delay > 0:
            real_key = Databus.get_real_key(key)
            self._future[real_key] = value
            time.sleep(delay)
            self._data[real_key] = self._future[real_key]
        result = []
        for cb in self._observer_map[key]:
            if sync:
                result.append(cb(key))
            else:
                cb(key)
        if sync:
            return result

    def observe_value(self, key, callback):
        assert hasattr(callback, '__call__')
        assert len(inspect.getargspec(callback)[0])
        if key not in self._observer_map:
            self._observer_map[key] = []
        self._observer_map[key].append(callback)

    def initialize(self, config_file):
        self.reset()
        assert self.initialized.isSet() is False
        logger.debug('Initializing databus using %s.', config_file)
        dom = etree.parse(config_file)
        entries = dom.xpath('//core/databus/key_value_mappings/*')
        for entry in entries:
            key = entry.attrib['name']
            value = entry.xpath('./value/text()')[0].strip()
            value_type = str(entry.xpath('./value/@type')[0])
            assert key not in self._data
            logging.debug('Initializing %s with %s as a %s.', key, value, value_type)
            if value_type == 'value':
                self.set_value(key, eval(value))
            elif value_type == 'function':
                namespace, _classname = value.rsplit('.', 1)
                params = entry.xpath('./value/@param')
                module = __import__(namespace, fromlist=[_classname])
                _class = getattr(module, _classname)
                if len(params) > 0:
                    # eval param to list
                    params = eval(params[0])
                    self.set_value(key, _class(*(tuple(params))))
                else:
                    self.set_value(key, _class())
            else:
                raise Exception('Unknown value type: {0}'.format(value_type))
        # influxdb config
        influx_config = dom.xpath('//core/influxdb')[0]
        host = influx_config.xpath('./host/text()')[0]
        port = influx_config.xpath('./port/text()')[0]
        username = influx_config.xpath('./username/text()')[0]
        password = influx_config.xpath('./password/text()')[0]
        database = influx_config.xpath('./database/text()')[0]
        self.client = InfluxDBClient(host, port, username, password, database)
        self.initialized.set()

    def get_shapshot(self):
        # takes a snapshot of the internal honeypot state and returns it as json.
        snapsnot = {}
        for key in self._data.keys():
            snapsnot[key] = self.get_value(key)
        return json.dumps(snapsnot)

    def reset(self):
        logger.debug('Resetting databus.')

        # if the class has a stop method call it.
        for value in self._data.values():
            if getattr(value, "stop", None):
                value.stop()

        self._data.clear()
        self._observer_map.clear()
        self.initialized.clear()
