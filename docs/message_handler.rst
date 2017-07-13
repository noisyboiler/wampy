The MessageHandler Class
============================

Every wampy ``Client`` requires a ``MessageHandler``. This is a class with a list of ``Messages`` it will accept and a "handle" method for each.

The default ``MessageHandler`` contains everything you need to use WAMP in your microservices, but you may want to add more behaviour such as logging messages, encrypting messages, appending meta data or custom authorisation.

If you want to define your own ``MessageHandler`` then you must subclass the default and override the "handle" methods for each ``Message`` customisation you need.

Note that whenever the ``Session`` receives a ``Message`` it calls ``handle_message`` on the ``MessageHandler``. You can override this if you want to add global behaviour changes. ``handle_message`` will delegate to specific handlers, e.g. ``handle_invocation``.

For example.

::

    from wampy.message_handler import MessageHandler


    class CustomHandler(MessageHandler):

        def handle_welcome(self, message_obj):
            # maybe do some auth stuff here
            super(CustomHandler, self).handle_welcome(message_obj)
            # and maybe then some other stuff now like alerting


There may be no need to even do what wampy does if your application already has patterns for handling WAMP messages! In which case override but don't call ``super`` - just do your own thing.

Then your Client should be initialised with an *instance* of the custom handler.

::

    from wampy.peers.clients import Client

    client = Client(message_handler=CustomHandler())
