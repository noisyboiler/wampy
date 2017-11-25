Contributing to wampy
----------------------

Contributions are very welcome!

### wampy style conventions

wampy follows the standard [PEP8 style guide for Python](http://www.python.org/dev/peps/pep-0008/) and the [PEP257](http://www.python.org/dev/peps/pep-0257/) for docstrings.

All source code is linted using the default configuration of [flake8](https://pypi.python.org/pypi/flake8).

### Imports

Please follow the following convention:

    # standard lib, straight `imports` first please
    import os
    import sys
    from itertools import cycle, repeat  # imports should be in alphabetical order

    # 3rd party imports
    import sqlalchemy
    from eventlet.green import urllib2

    # wampy imports
    from wampy.constants import (
        CROSSBAR_DEFAULT, DEFAULT_ROLES, DEFAULT_REALM,  # trailing commas are appreciated
    )
    from wampy.session import Session
    from wampy.messages import Abort, Challenge


### Line Length

wampy especially enjoys line lengths <= 79 chars and longer lines crafted with appropriate lines breaks.

For example, above, wampy always drops import lines longer than 79 chars on to a new line and never uses backslashes - parenthesis are always preferred.

Please never use backslashes.
