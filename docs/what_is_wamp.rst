What is WAMP?
=============

The `WAMP Protocol`_ is a powerful tool for your web applications and microservices - else just for your free time, fun and games!

**WAMP** facilitates communication between independent applications over a common "router". An actor in this process is called a **Peer**, and a **Peer** is either a **Client** or the **Router**.

**WAMP** messaging occurs between **Clients** over the **Router** via **Remote Procedure Call (RPC)** or the **Publish/Subscribe** pattern. As long as your **Client** knows how to connect to a **Router** it does not then need to know anything further about other connected **Peers** beyond a shared string name for an endpoint or **Topic**, i.e. it does not care where another **Client** application is, how many of them there might be, how they might be written or how to identify them. This is more simple than other messaging protocols, such as AMQP for example, where you also need to consider exchanges and queues in order to explicitly connect to other actors from your applications.

**WAMP** is most commonly a WebSocket subprotocol (runs on top of WebSocket) that uses JSON as message serialization format. However, the protocol can also run with MsgPack as serialization, run over raw TCP or in fact any message based, bidirectional, reliable transport - but **wampy** (currently) runs over websockets only.

For further reading please see some of the popular blog posts on WAMP such as http://tavendo.com/blog/post/is-crossbar-the-future-of-python-web-apps/.

.. _WAMP Protocol: http://wamp-proto.org/
