# wampy

## A Python WAMP Implementation.

The WAMP protocol connects Clients via RPC or Pub/Sub over a Router.

A Client is some kind of application that __calls__ or __subscribes__ to another Client, else provides something for others to call or subscribe to. These are "Roles" that are performed by a Client, and they are referred to as *Caller*, *Callee*, *Publisher* and *Subscriber*. 

A Router is another type of application - a message broker - that is either a *Broker* or a *Dealer*, and highly likely to be Crossbar.io.

Whatever application you're dealing with, WAMP refers to these as a __Peer__.

With __wampy__, you can (so far) create Peers to implement the WAMP roles: Callee, Caller and Dealer.

### Quickstart: wampy from a Python console.

Before any messaging can happen you need a Router. This is a Peer that implements the Dealer or Broker roles, or both. Messages are then routed between Clients over an administritive domain called a "realm".

For a quickstart I suggest that you use Crossbar.io and start it up on the default __host__ and __port__ with the default __realm__ and __roles__. See the [Crossbar.io docs](http://crossbar.io/docs/Quick-Start/) for the instructions of this.

Then open a Python console.

	In [1]: from wampy.peers import WampRouter, WampClient

	In [2]: from wampy.rpc import rpc

	In [3]: from wampy.constants import (
	   ...: 	DEFAULT_REALM, DEFAULT_ROLES, DEFAULT_HOST, DEFAULT_PORT)

	In [4]: crossbar = WampRouter(
	   ...: 	name="Crossbar", host=DEFAULT_HOST, port=DEFAULT_PORT,
	   ...: 	realm=DEFAULT_REALM)

	In [5]: import datetime

	In [6]: class DateService(WampClient):
	   ...: 	""" A service that tells you todays date """
	   ...: 	
	   ...: 	@rpc
	   ...: 	def get_todays_date(self):
	   ...: 	    return datetime.date.today().isoformat()

	In [7]: service = DateService(
	   ...:		name="Date Service", router=crossbar,
	   ...: 	realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
	   ...: )

	In [8]: service.start()

	In [9]: service.session.id
	Out[9]: 3941615218422338

If a Peer implements the "Callee" Role, then by starting the Peer you instruct the Peer to register its RPC entrypoints with the Router.

	In [10]: from wampy.registry import get_registered_entrypoints

	In [11]: get_registered_entrypoints()
	Out[11]: {2010994119734585: (__main__.DateService, 'get_todays_date')}

Any method of the Peer decorated with @rpc will have been registered as publically availabile over the Router.

	In [12]: from wampy.peers.clients import RpcClient

	In [13]: client = RpcClient(
	    ...: 	name="Caller", router=crossbar,
	    ...: 	realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
	    ...: )

The built in stand alone client knows about the entrypoints made available by the ``DateService`` and using it you can call them directly.

	In [14]: client.start()  # note that you can context-manage clients and avoid this step!

	In [15]: client.rpc.get_todays_date()
	Out [15]: u'2016-05-14'

If you don't context-manage your client, then you do have to explicitly call ``stop`` in order to gracefully disassociate yourself from the router, but also to tidy up the green threads and connections.

	In [16]: client.stop()

That's about it so far.

	In [17]: exit()
