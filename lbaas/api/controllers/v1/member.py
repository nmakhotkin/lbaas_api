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

from oslo_log import log as logging
import pecan
from pecan import hooks
from pecan import rest
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from lbaas.api.controllers import resource
from lbaas.db.v1 import api as db_api
from lbaas.utils import rest_utils


LOG = logging.getLogger(__name__)


class Member(resource.Resource):
    """Member resource."""

    id = wtypes.text
    name = wtypes.text

    address = wtypes.text
    protocol_port = wtypes.IntegerType()
    description = wtypes.text

    tags = [wtypes.text]

    created_at = wtypes.text
    updated_at = wtypes.text


class Members(resource.Resource):
    """A collection of Members."""

    members = [Member]


class MembersController(rest.RestController, hooks.HookController):
    @rest_utils.wrap_wsme_controller_exception
    @wsme_pecan.wsexpose(Member, wtypes.text)
    def get(self, name):
        """Return the named member."""
        LOG.info("Fetch member [name=%s]" % name)

        db_model = db_api.get_member(name)

        return Member.from_dict(db_model.to_dict())

    @rest_utils.wrap_wsme_controller_exception
    @wsme_pecan.wsexpose(Member, wtypes.text, body=Member)
    def put(self, id, member):
        """Update a member."""
        LOG.info("Update member [member_name=%s]" % member.name)

        values = member.to_dict()

        return Member.from_dict(
            db_api.update_member(
                member.name,
                values
            ).to_dict()
        )

    @rest_utils.wrap_wsme_controller_exception
    @wsme_pecan.wsexpose(Member, body=Member, status_code=201)
    def post(self, member):
        """Create a new member."""
        LOG.info("Create member [member_name=%s]" % member.name)

        pecan.response.status = 201

        values = member.to_dict()

        return Member.from_dict(db_api.create_member(values).to_dict())

    @rest_utils.wrap_wsme_controller_exception
    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, name):
        """Delete the named member."""
        LOG.info("Delete member [name=%s]" % name)

        db_api.delete_member(name)

    @wsme_pecan.wsexpose(Members)
    def get_all(self):
        """Return all members."""
        LOG.info("Fetch members.")

        members_list = [
            Member.from_dict(db_model.to_dict())
            for db_model in db_api.get_members()
        ]

        return Members(members=members_list)