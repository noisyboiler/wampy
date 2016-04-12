# wampy

## Experimental (and incomplete) WAMP Implementation. WIP.

The WAMP protocol connects Clients through either RPC or pub/sub over a Router. A Client is some kind of application, maybe a Caller, maybe a Callee, else a Publisher or a Subscriber. A Router is another type of application - a message broker - and highly likely to be Crossbar. Whatever application you're dealing with, WAMP refers to these as a "Peer".

With this project you can (so far) create and register Peers to implement the WAMP roles: Callee, Caller and Dealer.

# Quickstart: A Router Peer

Before any messaging can happen you need to register a Peer to act as your router, which must implement the Dealer or Broler roles. or both.

For example, using the built-in Crossbar router.

	In [1]: from wampy import register_peer

	In [2]: from wampy.testing.routers import Crossbar

	In [3]: crossbar = Crossbar(
	   ...: 	host='localhost',
       ...: 	config_path='./wampy/testing/routers/config.json',
       ...: 	crossbar_directory='./'
       ...: )

    In [4]: register_peer(crossbar)

    ... watch plenty of Crossbar.io logging ouput fly by....

You can then begin a Session with the Router.

	In [5]: from wampy.session import Session

	In [6]: session = Session(crossbar)

From instantiation you have a TCP connection to the router, upgraded to a websocket. The final step to establish a WAMP session is explicit and involves message transfer.

	In [7]: session.begin()

	2016-04-11 18:31:16,676 - wampy.wamp.session - INFO - sending "HELLO" message
	2016-04-11 18:31:16,678 - wampy.wamp.session - INFO - received "WELCOME" message
	2016-04-11 18:31:16,678 - wampy.wamp.session - INFO - session started with ID: 1602973961705819

You'll be assigned the session ID.

	In [8]: session.id
	Out[10]: 1602973961705819

With this session you can make RPC calls to any Calle registered with the router.

# Quickstart: RPC call


Just ensure that your application impliments the Peer interface.

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
