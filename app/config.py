"""Application configuration for the Flask rewrite of the original Node.js server.

This module implements the *Configuration Object* design pattern for the Python 3
Flask application that replaces the original single-file Node.js HTTP server
(``server.js``). Every value that was hardcoded inline in ``server.js`` is
centralized here in a single :class:`Config` class and preserved **exactly**, so
that the rewritten application reproduces the original's observable behavior
byte-for-byte.

The module is the leaf/foundation of the ``app`` package import graph: it imports
nothing and is imported (directly or indirectly) by the application factory
(``app/__init__.py``), the process entrypoints (``server.py`` and ``wsgi.py``),
and the catch-all route handler (``app/main/routes.py``).

Origin mapping (line references are to ``server.js`` in the repository root)::

    server.js source        value                   Config attribute
    ----------------------  ----------------------  ----------------
    L3  hostname            '127.0.0.1'             HOST
    L4  port                3000                    PORT
    L8  Content-Type        'text/plain'            CONTENT_TYPE
    L9  res.end(...)        'Hello, World!\\n'       RESPONSE_BODY

The HTTP status code (``200`` at ``server.js`` L7) is intentionally *not* stored
here; it is applied directly by the route handler, mirroring the source, which
sets ``res.statusCode`` inline in the request callback.
"""


class Config:
    """Centralized configuration constants ported verbatim from ``server.js``.

    Flask loads this class via ``app.config.from_object(Config)`` in the
    application factory. Because ``from_object`` copies **only UPPERCASE**
    attributes into ``app.config``, all four attributes defined below are
    uppercase and therefore become available at request time as
    ``current_app.config['HOST' | 'PORT' | 'RESPONSE_BODY' | 'CONTENT_TYPE']``.

    The values are a 1:1 relocation of the constants that were hardcoded inline
    in the original Node.js server. None of them may be changed, reformatted, or
    "improved" without breaking the byte-for-byte behavioral parity that this
    migration is required to preserve.
    """

    # --- Network binding (server.js L3-L4) --------------------------------
    # Loopback interface the server binds to. Kept as the exact string from
    # ``server.js`` L3 so that both the bind address and the startup-log
    # f-string ("http://127.0.0.1:3000/") render identically to the Node
    # original.
    HOST = '127.0.0.1'

    # TCP port the server listens on. Deliberately an ``int`` (not a string):
    # it is passed to ``app.run(port=...)`` (which requires an integer) and is
    # interpolated into the startup-log f-string. This value overrides Flask's
    # default development port of 5000 so the rewrite binds 127.0.0.1:3000
    # exactly like ``server.js`` L4.
    PORT = 3000

    # --- Fixed HTTP response contract (server.js L8-L9) -------------------
    # Response body returned for *every* request, on *every* path and *every*
    # HTTP method. The trailing newline is significant: 'Hello, World!\n' is
    # exactly 14 bytes, which reproduces the same ``Content-Length: 14`` header
    # the Node server emitted (server.js L9).
    RESPONSE_BODY = 'Hello, World!\n'

    # ``Content-Type`` header value, passed verbatim to Flask's
    # ``Response(..., content_type=CONTENT_TYPE)``. It is exactly 'text/plain'
    # with **no** charset suffix: using Flask's ``mimetype=`` argument instead
    # would cause Werkzeug to append '; charset=utf-8', which would break
    # byte-for-byte parity with ``server.js`` L8.
    CONTENT_TYPE = 'text/plain'
