from charms.reactive import Endpoint, when, set_flag


class ZookeeperProvides(Endpoint):

    @when('endpoint.{endpoint_name}.joined')
    def joined(self):
        set_flag(self.expand_name('available'))

    def configure(self, host, port):
        """
        Configure the elasticsearch relation by providing:
            - host
            - port
        """

        for relation in self.relations:
            relation.to_publish.update({
                'host': host,
                'port': port,
            })
