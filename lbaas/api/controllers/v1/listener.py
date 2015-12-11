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
from pecan import rest
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from lbaas.api.controllers import resource
from lbaas.db.v1 import api as db_api
from lbaas.drivers import driver
from lbaas import exceptions as exceptions
from lbaas.utils import rest_utils


LOG = logging.getLogger(__name__)


class Listener(resource.Resource):
    """Environment resource."""

    id = wtypes.text
    name = wtypes.text
    description = wtypes.text
    protocol = wtypes.text
    protocol_port = wtypes.IntegerType()
    algorithm = wtypes.text

    created_at = wtypes.text
    updated_at = wtypes.text


class Listeners(resource.Resource):
    """A collection of Environment resources."""

    listeners = [Listener]


class ListenersController(rest.RestController):
    @wsme_pecan.wsexpose(Listeners)
    def get_all(self):
        """Return all listeners."""

        LOG.info("Fetch listeners.")

        listeners = [
            Listener.from_dict(db_model.to_dict())
            for db_model in db_api.get_listeners()
        ]

        return Listeners(listeners=listeners)

    @rest_utils.wrap_wsme_controller_exception
    @wsme_pecan.wsexpose(Listener, wtypes.text)
    def get(self, name):
        """Return the named listener."""
        LOG.info("Fetch listener [name=%s]" % name)

        db_model = db_api.get_listener(name)

        return Listener.from_dict(db_model.to_dict())

    @rest_utils.wrap_wsme_controller_exception
    @wsme_pecan.wsexpose(Listener, body=Listener, status_code=201)
    def post(self, listener):
        """Create a new listener."""
        LOG.info("Create listener [listener=%s]" % listener)

        if not (listener.name and listener.protocol_port
                and listener.protocol):
            raise exceptions.InputException(
                'You must provide at least name, protocol_port and'
                ' protocol of the listener.'
            )

        if not listener.algorithm:
            listener.algorithm = 'roundrobin'

        lb_driver = driver.LB_DRIVER()

        with db_api.transaction():
            db_model = lb_driver.create_listener(listener.to_dict())

            lb_driver.apply_changes()

        return Listener.from_dict(db_model.to_dict())

    @rest_utils.wrap_wsme_controller_exception
    @wsme_pecan.wsexpose(Listener, body=Listener)
    def put(self, listener):
        """Update an listener."""
        if not listener.name:
            raise exceptions.InputException(
                'Name of the listener is not provided.'
            )

        LOG.info(
            "Update listener [name=%s, listener=%s]" %
            (listener.name, listener)
        )

        lb_driver = driver.LB_DRIVER()

        with db_api.transaction():
            db_model = lb_driver.update_listener(
                listener.name,
                listener.to_dict()
            )

            lb_driver.apply_changes()

        return Listener.from_dict(db_model.to_dict())

    @rest_utils.wrap_wsme_controller_exception
    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, name):
        """Delete the named listener."""
        LOG.info("Delete listener [name=%s]" % name)

        lb_driver = driver.LB_DRIVER()

        with db_api.transaction():
            lb_driver.delete_listener(name)

            lb_driver.apply_changes()
