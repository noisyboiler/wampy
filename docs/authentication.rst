Authentication Methods
======================

The Realm is a WAMP routing and administrative domain, optionally protected by authentication and authorization.

In the WAMP Basic Profile without session authentication the Router will reply with a "WELCOME" or "ABORT" message.

::

       ,------.          ,------.
       |Client|          |Router|
       `--+---'          `--+---'
          |      HELLO      |
          | ---------------->
          |                 |
          |     WELCOME     |
          | <----------------
       ,--+---.          ,--+---.
       |Client|          |Router|
       `------'          `------'

The Advanced router Profile provides some authentication options at the WAMP level - although your app may choose to use transport level auth (e.g. cookies or TLS certificates) or implement its own system (e.g. on the remote procedure).

::

        ,------.          ,------.
        |Client|          |Router|
        `--+---'          `--+---'
           |      HELLO      |
           | ---------------->
           |                 |
           |    CHALLENGE    |
           | <----------------
           |                 |
           |   AUTHENTICATE  |
           | ---------------->
           |                 |
           | WELCOME or ABORT|
           | <----------------
        ,--+---.          ,--+---.
        |Client|          |Router|
        `------'          `------'


Challenge Response Authentication
---------------------------------

WAMP Challenge-Response ("WAMP-CRA") authentication is a simple, secure authentication mechanism using a shared secret. The client and the server share a secret. The secret never travels the wire, hence WAMP-CRA can be used via non-TLS connections. 

wampy needs the secret to be set as an environment variable against the key ``WAMPYSECRET`` on deployment or in the test environment (if testing auth) otherwise a ``WampyError`` will be raised. In future a ``Client`` could take configuration on startup.

The Router must also be configured to expect Users and by what auth method.

For the Client you can instantiate the ``Client`` with ``roles`` which can take ``authmethods`` and ``authid``.

::

    roles = {
        'roles': {
            'subscriber': {},
            'publisher': {},
            'callee': {
                'shared_registration': True,
            },
            'caller': {},
        },
        'authmethods': ['wampcra']  # where "anonymous" is the default
        'authid': 'your-username-or-identifier'
    }

    client = Client(roles=roles)

And the Router would include something like...

::

    "auth": {
        "wampcra": {
            "type": "static",
            "role": "wampy",
            "users": {
                "your-username-or-identifier": {
                    "secret": "prq7+YkJ1/KlW1X0YczMHw==",
                    "role": "wampy",
                    "salt": "salt123",
                    "iterations": 100,
                    "keylen": 16,
                },
                "someone-else": {
                    "secret": "secret2",
                    "role": "wampy",
                    ...
                },
                ...
            }
        },
        "anonymous": {
            "type": "static",
            "role": "wampy"
        }
    }

with permissions for RPC and subscriptions optionally defined. See the included testing `config`_ for a more complete example.

.. _config: https://github.com/noisyboiler/wampy/master/wampy/testing/config.static.auth.json
