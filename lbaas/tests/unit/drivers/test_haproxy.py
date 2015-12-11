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

import mock

from lbaas.db.v1.sqlalchemy import api as db_api
from lbaas.drivers import haproxy as driver
from lbaas import exceptions as exc
from lbaas.tests.unit import base as test_base
from lbaas.utils import file_utils


class HAProxyDriverTest(test_base.DbTestCase):
    @mock.patch.object(file_utils, 'replace_file')
    def test_create_listener(self, replace_file):
        haproxy = driver.HAProxyDriver()

        haproxy.create_listener({
            'name': 'test_listener',
            'description': 'my test settings',
            'protocol': 'http',
            'protocol_port': 80,
            'algorithm': 'roundrobin'
        })

        listener = db_api.get_listener('test_listener')

        self.assertEqual('roundrobin', listener.algorithm)

        config_data = replace_file.call_args[0][1]

        self.assertIn(
            'listen %s 0.0.0.0:%s' % (listener.name, listener.protocol_port),
            config_data
        )

    @mock.patch.object(file_utils, 'replace_file')
    def test_create_member(self, replace_file):
        haproxy = driver.HAProxyDriver()

        # Create a listener first.
        haproxy.create_listener({
            'name': 'test_listener',
            'description': 'my test settings',
            'protocol': 'http',
            'protocol_port': 80,
            'algorithm': 'roundrobin'
        })

        listener = db_api.get_listener('test_listener')

        haproxy.create_member(
            listener.name,
            {
                'name': 'member1',
                'address': '10.0.0.1',
                'protocol_port': 80,
            }
        )

        member = db_api.get_member('member1')

        self.assertEqual('10.0.0.1', member.address)

        self.assertEqual(2, replace_file.call_count)

        config_data = replace_file.call_args[0][1]
        self.assertIn(
            '\tserver %s %s:%s check' %
            (member.name, member.address, member.protocol_port),
            config_data
        )

    @mock.patch.object(file_utils, 'replace_file')
    def test_update_listener(self, replace_file):
        haproxy = driver.HAProxyDriver()

        haproxy.create_listener({
            'name': 'test_listener',
            'description': 'my test settings',
            'protocol': 'http',
            'protocol_port': 80,
            'algorithm': 'roundrobin'
        })

        listener = db_api.get_listener('test_listener')

        haproxy.update_listener(listener.name, {'protocol_port': 8080})

        config_data = replace_file.call_args[0][1]

        self.assertIn(
            'listen %s 0.0.0.0:%s' % (listener.name, 8080),
            config_data
        )

    @mock.patch.object(file_utils, 'replace_file')
    def test_update_member(self, replace_file):
        haproxy = driver.HAProxyDriver()

        # Create a listener first.
        haproxy.create_listener({
            'name': 'test_listener',
            'description': 'my test settings',
            'protocol': 'http',
            'protocol_port': 80,
            'algorithm': 'roundrobin'
        })

        listener = db_api.get_listener('test_listener')

        member = haproxy.create_member(
            listener.name,
            {
                'name': 'member1',
                'address': '10.0.0.1',
                'protocol_port': 80,
            }
        )

        self.assertEqual(80, member.protocol_port)

        haproxy.update_member(member.name, {'protocol_port': 8080})

        config_data = replace_file.call_args[0][1]

        self.assertIn(
            '\tserver %s %s:%s check' % (member.name, member.address, 8080),
            config_data
        )

    @mock.patch.object(file_utils, 'replace_file')
    def test_delete_listener(self, replace_file):
        haproxy = driver.HAProxyDriver()

        # Create a listener first.
        haproxy.create_listener({
            'name': 'test_listener',
            'description': 'my test settings',
            'protocol': 'http',
            'protocol_port': 80,
            'algorithm': 'roundrobin'
        })

        listener = db_api.get_listener('test_listener')

        config_data = replace_file.call_args[0][1]

        self.assertIn(
            'listen %s 0.0.0.0:%s' % (listener.name, listener.protocol_port),
            config_data
        )

        haproxy.delete_listener(listener.name)

        config_data = replace_file.call_args[0][1]

        self.assertNotIn(
            'listen %s 0.0.0.0:%s' % (listener.name, listener.protocol_port),
            config_data
        )
        self.assertRaises(
            exc.NotFoundException,
            db_api.get_listener,
            listener.name
        )

    @mock.patch.object(file_utils, 'replace_file')
    def test_delete_member(self, replace_file):
        haproxy = driver.HAProxyDriver()

        # Create a listener first.
        haproxy.create_listener({
            'name': 'test_listener',
            'description': 'my test settings',
            'protocol': 'http',
            'protocol_port': 80,
            'algorithm': 'roundrobin'
        })

        listener = db_api.get_listener('test_listener')

        haproxy.create_member(
            listener.name,
            {
                'name': 'member1',
                'address': '10.0.0.1',
                'protocol_port': 80,
            }
        )

        member = db_api.get_member('member1')

        config_data = replace_file.call_args[0][1]

        self.assertIn(
            '\tserver %s %s:%s check' %
            (member.name, member.address, member.protocol_port),
            config_data
        )

        haproxy.delete_member(member.name)

        config_data = replace_file.call_args[0][1]

        self.assertNotIn(
            '\tserver %s %s:%s check' %
            (member.name, member.address, member.protocol_port),
            config_data
        )
        self.assertRaises(
            exc.NotFoundException,
            db_api.get_member,
            member.name
        )
