"""Development / parity entrypoint for the Flask rewrite of the Node.js server.

Python counterpart of ``node server.js``: it builds the app via the Application
Factory and, when run directly, reproduces the source's listener/log block
(``server.js`` L12-L14), which bound ``127.0.0.1:3000`` and then logged
``Server running at http://127.0.0.1:3000/`` from its on-success callback.

Request handling is not here: every request is served by the universal catch-all
route in :mod:`app.main.routes`; the response contract and network constants live
in :class:`app.config.Config`. Host/port come from ``Config`` (overriding Flask's
default 5000). ``app`` is built at module level so the module imports without
opening a socket (both entrypoints share this contract; the ``__main__`` guard
below is what starts the server).
"""

import logging

from werkzeug.serving import make_server

from app import create_app
from app.config import Config

# Built once at import; create_app() opens no socket, so import stays side-effect
# free and the module is safe to import from a test harness.
app = create_app()


if __name__ == "__main__":
    # Suppress Werkzeug's per-request access log. The Node source logged only
    # the startup line, never per-request lines (server.js L13), so silencing
    # the access log restores that parity AND avoids writing request targets --
    # which can carry query-string secrets/PII (CWE-532) -- to stderr, even
    # though the handler ignores request data entirely. Genuine server errors
    # still surface at ERROR level. Scoped to this development/parity
    # entrypoint only; the WSGI production path (wsgi.py) is untouched.
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    # Parity-critical ordering (mirrors server.js L12-L14: listen -> on-success
    # callback -> serve). make_server() binds the socket immediately and raises
    # OSError on a port collision BEFORE the startup line prints, so the line
    # is emitted only after a confirmed bind -- never a false success. A bind
    # failure propagates as OSError -> nonzero exit with no line, mirroring
    # Node's EADDRINUSE.
    #
    # threaded=True serves each request in its own thread so a slow or
    # incomplete client cannot block other requests, matching the Node event
    # loop's non-blocking behavior and honoring the "performance not impacted"
    # rule. (Werkzeug's make_server defaults to a single-threaded server, which
    # would serialize requests and let one stalled client stall all others;
    # Flask's app.run() likewise defaults threaded=True.) No debug/reloader: a
    # single, stable process whose observable HTTP contract is unchanged.
    httpd = make_server(Config.HOST, Config.PORT, app, threaded=True)

    # flush=True emits the line immediately (unbuffered), so it is observable
    # through a pipe or redirect the instant the server is up -- as Node's
    # console.log was -- instead of being stranded in a stdio buffer until the
    # process exits.
    print(f"Server running at http://{Config.HOST}:{Config.PORT}/", flush=True)

    httpd.serve_forever()
