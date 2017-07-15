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

The secret must be set as an environment variable against the key ``WAMPYSECRET`` on deployment otherwise a ``WampyError`` will be raised.

The Router must be configured to expect users and the wampy Client given the corresponding configutred Roles.

For the Client, e.g.

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

See the included testing `config`_ for a more complete example.

.. _config: https://github.com/noisyboiler/wampy/master/wampy/testing/config.static.auth.json
