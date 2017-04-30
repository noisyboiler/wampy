Subscribing to a Topic
======================

You need a long running wampy application process for this.

::

    from wampy.peers.clients import Client
    from wampy.roles import subscribe


    class WampyApp(Client):

        @subscribe(topic="topic-name")
        def weather_events(self, topic_data):
            # do something with the ``topic_data`` here
            pass


See `runnning a wampy application`_ for executing the process.


.. _runnning a wampy application: a_wampy_application.html#running-the-application
