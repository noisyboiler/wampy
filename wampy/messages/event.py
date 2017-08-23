# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class Event(object):
    """ When a Subscriber_is deemed to be a receiver, the Broker sends
    the Subscriber an "EVENT" message:

        [EVENT, SUBSCRIBED.Subscription|id, PUBLISHED.Publication|id,
         Details|dict]

            or

        [EVENT, SUBSCRIBED.Subscription|id, PUBLISHED.Publication|id,
               Details|dict, PUBLISH.Arguments|list]

            or

        [EVENT, SUBSCRIBED.Subscription|id, PUBLISHED.Publication|id,
         Details|dict, PUBLISH.Arguments|list, PUBLISH.ArgumentKw|dict]

    """
    WAMP_CODE = 36
    name = "event"

    def __init__(
            self, subscription_id, publication_id, details_dict,
            publish_args=None, publish_kwargs=None,
    ):

        super(Event, self).__init__()

        self.subscription_id = subscription_id
        self.publication_id = publication_id
        self.details = details_dict
        self.publish_args = publish_args or []
        self.publish_kwargs = publish_kwargs or {}

    @property
    def message(self):
        return [
            self.WAMP_CODE, self.subscription_id, self.publication_id,
            self.details, self.publish_args, self.publish_kwargs,
        ]
