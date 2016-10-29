from wampy.peers.web.client import WebClient
from wampy.roles.callee import register_rpc


MAX_META_COLLECTION_SIZE = 100


class WebApplication(WebClient):

    @register_rpc(invocation_policy="roundrobin")
    def get_meta(self):
        meta = {
            'name': self.name,
            'subscriptions': self.subscription_map.keys(),
            'registrations': self.registration_map.keys(),
        }

        return meta

    def collect_client_meta_data(self):
        collection = {}
        client_count = 0

        while True:
            meta = self.rpc.get_meta()
            peer_name = meta['name']
            if peer_name in collection:
                # while wampy servies do not announce themselves, we
                # are forced to assume that we're the only client calling
                # ``get_meta`` and that we have now completed the
                # roundrobin of clients.
                break

            collection[peer_name] = meta
            client_count += 1

            if client_count > MAX_META_COLLECTION_SIZE:
                self.logger.warning(
                    "max clients reached during ``get_meta`` roundrobin"
                )

                break

        return collection
