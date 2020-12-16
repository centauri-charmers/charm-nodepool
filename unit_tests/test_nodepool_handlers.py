# Copyright 2018 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import print_function

import reactive.nodepool as handlers
import charms_openstack.test_utils as test_utils


class TestRegisteredHooks(test_utils.TestRegisteredHooks):

    def test_hooks(self):
        # hook_set = {
        #     'when': {
        #         'render_things': ('amqp.available',
        #                           'shared-db.available',),
        #     },
        # }
        defaults = []
        hook_set = {
            'when_not': {
                'configure': ('nodepool.configured',),
                'wait_for_zookeeper': ('endpoint.zookeeper.available',),
                'install_nodepool': ('nodepool.installed',),
                'connect_zookeeper': ('endpoint.zookeeper.joined',),
                'add_nodepool_user': ('nodepool.user.created',),
                'get_creds': ('charm.openstack.creds.set',),
                'configure_nodepool_cloud': ('nodepool.cloud.configured',),
                'enable_nodepool': ('nodepool.started',),
            },
            'when': {
                'install_nodepool': (
                    'apt.installed.python3-pip',),
                'configure': (
                    'nodepool.installed',
                    'endpoint.zookeeper.available',
                    'nodepool.user.created',
                    'nodepool.cloud.configured',
                    'endpoint.zookeeper.changed',),
                'wait_for_zookeeper': (
                    'nodepool.installed', 'endpoint.zookeeper.joined',),
                'set_ready': (
                    'nodepool.started',),
                'connect_zookeeper': ('nodepool.installed',),
                'restart_services': ('service.nodepool.restart',),
                'update_creds': (
                    'config.changed.username',
                    'config.changed.password',),
                'configure_nodepool_cloud': (
                    'charm.openstack.creds.set',
                    'nodepool.user.created',),
                'enable_nodepool': (
                    'nodepool.configured', 'nodepool.user.created',),
            }
        }
        # test that the hooks were registered via the
        # reactive.nodepool_scheduler handlers
        self.registered_hooks_test_helper(handlers, hook_set, defaults)
