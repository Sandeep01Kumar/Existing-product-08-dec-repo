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

from werkzeug.serving import make_server

from app import create_app
from app.config import Config

# Built once at import; create_app() opens no socket, so import stays side-effect
# free and the module is safe to import from a test harness.
app = create_app()


if __name__ == "__main__":
    # Parity-critical ordering (mirrors server.js L12-L14: listen -> on-success
    # callback -> loop). make_server() binds the socket immediately and raises
    # OSError on a port collision BEFORE the banner prints, so the success line
    # is emitted only after a confirmed bind -- never a false success. (app.run()
    # blocks in its loop and cannot print after binding; it wraps this same
    # make_server + serve_forever internally.) No debug/reloader: single process,
    # default threading, so the observable HTTP contract is unchanged. A bind
    # failure propagates as OSError -> nonzero exit with no banner, mirroring
    # Node's EADDRINUSE.
    httpd = make_server(Config.HOST, Config.PORT, app)
    print(f"Server running at http://{Config.HOST}:{Config.PORT}/")
    httpd.serve_forever()
