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

import copy
import datetime
import mock

from lbaas.db.v1 import api as db_api
from lbaas.db.v1.sqlalchemy import models
from lbaas import exceptions as exc
from lbaas.tests.unit.api import base


MEMBER_DB = models.Member(
    id='123',
    name='member',
    tags=['deployment', 'demo'],
    address='10.0.0.1',
    protocol_port=80,
    created_at=datetime.datetime(1970, 1, 1),
    updated_at=datetime.datetime(1970, 1, 1)
)

MEMBER = {
    'id': '123',
    'name': 'member',
    'tags': ['deployment', 'demo'],
    'address': '10.0.0.1',
    'protocol_port': 80,
    'created_at': '1970-01-01 00:00:00',
    'updated_at': '1970-01-01 00:00:00'
}

UPDATED_MEMBER_DB = copy.copy(MEMBER_DB)
UPDATED_MEMBER = copy.deepcopy(MEMBER)

MOCK_MEMBER = mock.MagicMock(return_value=MEMBER_DB)
MOCK_MEMBERS = mock.MagicMock(return_value=[MEMBER_DB])
MOCK_UPDATED_MEMBER = mock.MagicMock(return_value=UPDATED_MEMBER_DB)
MOCK_DELETE = mock.MagicMock(return_value=None)
MOCK_EMPTY = mock.MagicMock(return_value=[])
MOCK_NOT_FOUND = mock.MagicMock(side_effect=exc.NotFoundException())
MOCK_DUPLICATE = mock.MagicMock(side_effect=exc.DBDuplicateEntryException())


class TestMembersController(base.FunctionalTest):
    @mock.patch.object(db_api, "get_member", MOCK_MEMBER)
    def test_get(self):
        resp = self.app.get('/v1/members/123')

        self.assertEqual(200, resp.status_int)
        self.assertDictEqual(MEMBER, resp.json)

    @mock.patch.object(db_api, "get_member", MOCK_NOT_FOUND)
    def test_get_not_found(self):
        resp = self.app.get('/v1/members/123', expect_errors=True)

        self.assertEqual(404, resp.status_int)

    @mock.patch.object(db_api, "update_member", MOCK_UPDATED_MEMBER)
    def test_put(self):
        resp = self.app.put_json(
            '/v1/members',
            UPDATED_MEMBER,
        )

        self.assertEqual(200, resp.status_int)
        self.assertEqual(UPDATED_MEMBER, resp.json)

    @mock.patch.object(db_api, "update_member", MOCK_NOT_FOUND)
    def test_put_not_found(self):
        resp = self.app.put_json(
            '/v1/members',
            UPDATED_MEMBER,
            expect_errors=True
        )

        self.assertEqual(404, resp.status_int)

    @mock.patch.object(db_api, "create_member", MOCK_MEMBER)
    def test_post(self):
        resp = self.app.post_json(
            '/v1/members',
            MEMBER,
        )

        self.assertEqual(201, resp.status_int)
        self.assertEqual(MEMBER, resp.json)

    @mock.patch.object(db_api, "create_member", MOCK_DUPLICATE)
    def test_post_dup(self):
        resp = self.app.post_json(
            '/v1/members',
            MEMBER,
            expect_errors=True
        )

        self.assertEqual(409, resp.status_int)

    @mock.patch.object(db_api, "delete_member", MOCK_DELETE)
    def test_delete(self):
        resp = self.app.delete('/v1/members/123')

        self.assertEqual(204, resp.status_int)

    @mock.patch.object(db_api, "delete_member", MOCK_NOT_FOUND)
    def test_delete_not_found(self):
        resp = self.app.delete('/v1/members/123', expect_errors=True)

        self.assertEqual(404, resp.status_int)

    @mock.patch.object(db_api, "get_members", MOCK_MEMBERS)
    def test_get_all(self):
        resp = self.app.get('/v1/members')

        self.assertEqual(200, resp.status_int)

        self.assertEqual(1, len(resp.json['members']))
        self.assertDictEqual(MEMBER, resp.json['members'][0])

    @mock.patch.object(db_api, "get_members", MOCK_EMPTY)
    def test_get_all_empty(self):
        resp = self.app.get('/v1/members')

        self.assertEqual(200, resp.status_int)

        self.assertEqual(0, len(resp.json['members']))