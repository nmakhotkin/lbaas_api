# Copyright 2015 - Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import itertools

from oslo_concurrency import processutils

from lbaas.db.v1 import api as db_api
from lbaas.drivers import base
from lbaas.utils import file_utils


class HAProxyDriver(base.LoadBalancerDriver):
    config_file = "/etc/haproxy/haproxy.cfg"
    config = []

    def __init__(self):
        self._sync_configuration()

    def _sync_configuration(self):
        pass

    def update_listener(self, listener):
        pass

    def delete_listener(self, name):
        pass

    def delete_member(self, listener_name, member_name):
        pass

    def create_listener(self, listener_dict):
        listener = db_api.create_listener(listener_dict)

        self._save_config()

        return listener

    def update_member(self, member):
        pass

    def create_member(self, listener_name, member_dict):
        listener = db_api.get_listener(listener_name)

        values = member_dict
        values['listener_id'] = listener.id

        member = db_api.create_member(values)

        self._save_config()

        return member

    def _save_config(self):
        conf = []
        conf.extend(_build_global())
        conf.extend(_build_defaults())

        for l in db_api.get_listeners():
            conf.extend(_build_listen(l))

        file_utils.replace_file(self.config_file, '\n'.join(conf))

    def apply_changes(self):
        cmd = 'sudo service haproxy restart'.split()
        return processutils.execute(*cmd)


def _build_global(user_group='nogroup'):
    opts = [
        'daemon',
        'user nobody',
        'group %s' % user_group,
        'log /dev/log local0',
        'log /dev/log local1 notice'
    ]

    return itertools.chain(['global'], ('\t' + o for o in opts))


def _build_defaults():
    opts = [
        'log global',
        'retries 3',
        'option redispatch',
        'timeout connect 5000',
        'timeout client 50000',
        'timeout server 50000',
    ]

    return itertools.chain(['defaults'], ('\t' + o for o in opts))


def _build_listen(listener):
    opts = [
        'mode %s' % listener.protocol,
        'stats enable',
        'balance %s' % listener.algorithm,
        'option httpclose'
    ]

    for mem in listener.members:
        opts += [
            'server %s %s:%s check'
            % (mem.name, mem.address, mem.protocol_port)
        ]

    listener_line = (
        'listen %s 0.0.0.0:%s' % (listener.name, listener.protocol_port)
    )

    return itertools.chain([listener_line], ('\t' + o for o in opts))
