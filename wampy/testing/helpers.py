import eventlet


def wait_for_subscriptions(client, number_of_subscriptions):
    while (
        len(client.session.subscription_map.keys()) < number_of_subscriptions
    ):
        eventlet.sleep()


def wait_for_registrations(client, number_of_registrations):
    while (
        len(client.session.registration_map.keys()) < number_of_registrations
    ):
        eventlet.sleep()
