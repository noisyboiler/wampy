wampy
=====

.. pull-quote ::

    WAMP RPC and Pub/Sub for your Python apps and microservices

This is a Python implementation of **WAMP** not requiring Twisted or asyncio, enabling use within classic blocking Python applications. It is a light-weight alternative to `autobahn`_.

With **wampy** you can quickly and easily create your own **WAMP** clients, whether this is in a web app, a microservice, a script or just in a Python shell.

**wampy** tries to provide an intuitive API for your **WAMP** messaging.

WAMP
----

Background to the Web Application Messaging Protocol of which wampy implements.

.. toctree::
   :maxdepth: 2

   what_is_wamp


User Guide
----------

Running a wampy application or interacting with any other WAMP application

.. toctree::
   :maxdepth: 2

   what_is_wampy
   a_wampy_application
   a_wampy_client
   publishing_to_a_topic
   subscribing_to_a_topic
   remote_procedure_calls
   testing

modules
-------

.. toctree::

	wampy.constants
	wampy.errors
	wampy.mixins
	wampy.session
	wampy.messages.call
	wampy.messages.hello
	wampy.messages.goodbye
	wampy.messages.subscribe
	wampy.messages.publish
	wampy.messages.yield
	wampy.messages.register
	wampy.peers.clients
	wampy.peers.routers
	wampy.roles.callee
	wampy.roles.caller
	wampy.roles.publisher
	wampy.roles.subscriber


.. automodule:: constants
    :noindex:

.. automodule:: errors
    :noindex:

.. automodule:: mixins
    :noindex:

.. automodule:: session
    :noindex:

.. automodule:: clients
    :noindex:

.. automodule:: routers
    :noindex:

.. automodule:: callee
    :noindex:

.. automodule:: caller
    :noindex:

.. automodule:: publisher
    :noindex:

.. automodule:: subscriber
    :noindex:

.. automodule:: subscribe
    :noindex:

.. automodule:: publish
    :noindex:

.. automodule:: yield_
    :noindex:


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _autobahn: http://autobahn.ws/python/
