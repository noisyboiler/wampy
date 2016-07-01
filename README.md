# wampy

## A Python WAMP Implementation.

The WAMP protocol connects Clients via RPC or Pub/Sub over a Router.

A Client is some kind of application that __calls__ or __subscribes__ to another Client, else provides something for others to call or subscribe to. These are "Roles" that are performed by a Client, and they are referred to as *Caller*, *Callee*, *Publisher* and *Subscriber*. 

A Router is another type of application - a message broker - that is either a *Broker* or a *Dealer* & and highly likely to be Crossbar.

Whatever application you're dealing with, WAMP refers to these as a __Peer__.

With __wampy__ you can create Peers to implement WAMP roles: Callee, Caller, Publisher, Subscriber, Broker and Dealer.

### Quickstart: wampy from a Python console.

Before any messaging can happen you need a Router. This is a Peer that implements the Dealer or Broker roles, or both. Messages are then routed between Clients over an administritive domain called a "realm".

I suggest that you use Crossbar.io and start it up on the default host and port with the default realm. See the [Crossbar.io docs](http://crossbar.io/docs/Quick-Start/) for the instructions of this.

Then open a Python console.

	In [1]: from wampy.peers.clients import WampClient

	In [2]: from wampy.peers.routers import WampRouter

	In [3]: from wampy.constants import DEFAULT_REALM, DEFAULT_ROLES

	In [4]: crossbar = WampRouter(
	   ...: 	name="Crossbar", host="localhost", port="8080", realm=DEFAULT_REALM)

	In [5]: class DateService(WampClient):
	   ...: 	""" A service that tells you todays date """
	   ...: 	
	   ...: 	@rpc
	   ...: 	def get_todays_date(self):
	   ...: 	    return datetime.date.today().isoformat()

	In [6]: service = DateService(
	   ...:		name="Date Service", router=crossbar,
	   ...: 	realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
	   ...: )

	In [7]: service.start()

	In [8]: service.session.id
	Out[8]: 3941615218422338

If a Peer implements the "Callee" Role, then by starting the Peer you instruct the Peer to register its RPC entrypoints with the Router.

	In [9]: from wampy.registry import get_registered_entrypoints
	Out[9]: {347361574427174: (wampy.testing.clients.callees.DateService, 'get_todays_date')}

Any method of the Peer decorated with @rpc will have been registered as publically availabile over the Router.

	In [10]: from wampy.peers.clients import RpcClient

	In [11]: client = RpcClient(
	    ...: 	name="Caller", router=crossbar,
	    ...: 	realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
	    ...: )

The built in stand alone client knows about the entrypoints made available by the ``DateService`` and using it you can call them directly.

	In [12]: client.rpc.get_todays_date()
	Out [12]: u'2016-05-14'

If you don't context-manage your client, then you do have to explicitly call ``stop`` in order to gracefully disassociate yourself from the router but also to tidy up the threads and connections.

	In [13]: client.stop()

That's about it so far.

	In [14]: exit()
