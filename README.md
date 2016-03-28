# wampy

## Experimental (and incomplete) WAMP Implementation. WIP.

The WAMP protocol connects Clients through either RPC or pub/sub over a Router. A Client is some kind of application, maybe a Caller, maybe a Callee, else a Publisher or a Subscriber. A Router is another type of application - a message broker - and highly likely to be Crossbar. Whatever application you're dealing with, WAMP refers to these as a "Peer".

With this project you can so far register Peers and communicate between them over RPC.

	In [1]: from wampy import register_peer

	In [2]: register_peer(MyCalleeApplication)

Just ensure that your application implements the Peer interface.

	In [1]: from wampy.interfaces import Peer

	In [2]: callee = CalleApp(Peer):
		...:	pass

And that you decorate your entrypoints appropriately.

	In [1]: from wampy.entrypoints import rpc

	In [2]: callee = CalleApp(Peer):
		...:     @rpc
		...:     def application_entrypoint(self):
		...:         """ An exposed method to be called over RPC """
		...:

You can test your applications by using the built-in Crossbar Router.

	In [1]: from wampy.testing import Crossbar

	In [2]: register_peer(Crossbar)

	... watch some Crossbar.io logging go past....
