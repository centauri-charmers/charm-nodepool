from charms.reactive import set_flag, clear_flag, when
from charms.reactive import Endpoint


class ZookeeperPeer(Endpoint):

    @when('endpoint.{endpoint_name}.joined')
    def peer_joined(self):
        set_flag(self.expand_name('available'))
