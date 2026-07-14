"""Application package for the Flask rewrite of the original Node.js server.

This module makes ``app`` a Python package and exposes the application's single
public entrypoint: the :func:`create_app` **Application Factory**. It is the
direct structural replacement for the ``http.createServer(...)`` bootstrap of
the original ``server.js`` (root, L6). Instead of creating a module-level global
server object at import time, ``create_app`` constructs and configures a fresh
:class:`flask.Flask` instance on demand. That indirection keeps the wiring
testable (each test can build an isolated app) and cleanly separates the four
concerns of the rewrite:

* **settings** live in :mod:`app.config` (the :class:`~app.config.Config` object),
* **request handling** lives in the ``main`` blueprint (:mod:`app.main`),
* **wiring** lives here (this factory), and
* **process startup** lives in the entrypoints (``server.py`` / ``wsgi.py``).

The factory performs no I/O, opens no sockets, and starts no server; it only
assembles the object graph. Binding to ``127.0.0.1:3000`` and printing the
startup banner are the responsibility of the entrypoints, which import
``create_app`` from this package (``from app import create_app``) and either call
``app.run(...)`` (``server.py``) or expose the returned object as the WSGI
callable ``wsgi:app`` (``wsgi.py``).

Import graph (acyclic)::

    server.py / wsgi.py
            |
            v
    app/__init__.py  (create_app)
        |         |
        v         v
    app.config   app.main (main_bp)
                     |
                     v
                app.main.routes  -> reads app.config via current_app.config

This module introduces **no** new externally observable behavior; it is pure
wiring that reproduces the Node bootstrap in a modular, testable form.
"""

# --- Explicit imports only (no star imports) -----------------------------------
# The WSGI application class provided by Flask. ``create_app`` returns an
# instance of this type.
from flask import Flask

# Centralized configuration object holding the constants ported verbatim from
# ``server.js`` (HOST, PORT, RESPONSE_BODY, CONTENT_TYPE). Loaded into the app's
# config via ``from_object`` below; only its UPPERCASE attributes are copied.
from app.config import Config

# The ``main`` blueprint carrying the application's sole request-handling flow.
#
# Importing ``main_bp`` from :mod:`app.main` triggers execution of
# ``app/main/__init__.py``, which — by deliberate design — performs a deferred
# import of ``app.main.routes`` at the bottom of that module to register the
# catch-all route on the blueprint. That deferred-import pattern is what breaks
# the circular dependency between the blueprint definition and its routes, so
# nothing special is required here beyond importing the blueprint object.
from app.main import main_bp


def create_app():
    """Create and configure the Flask application (Application Factory).

    Builds a fresh :class:`flask.Flask` instance, loads the centralized
    :class:`~app.config.Config` values into ``app.config``, and registers the
    ``main`` blueprint so that every incoming request is handled by the
    universal catch-all route (the direct analogue of the source server's
    single ``http.createServer`` callback).

    The function takes no arguments and performs no network or startup side
    effects — it purely assembles and returns the configured application, which
    keeps it safe to call from both the development entrypoint (``server.py``)
    and the production WSGI entrypoint (``wsgi.py``).

    Returns:
        flask.Flask: A fully-configured application instance ready to be run by
        ``app.run(...)`` (development/parity) or served by a production WSGI
        server as ``wsgi:app`` (e.g. gunicorn or waitress).
    """
    # Instantiate the WSGI application. ``__name__`` gives Flask the correct
    # import name for resolving the package's root path.
    #
    # ``static_folder=None`` disables Flask's default ``/static/<path:filename>``
    # route. This server serves no static assets -- it returns one fixed
    # ``text/plain`` body for every request -- and the default static route
    # would otherwise shadow the catch-all for its own methods. In particular it
    # would answer ``OPTIONS /static/...`` with Flask's automatic empty
    # ``Allow`` response instead of the universal ``Hello, World!\n`` body,
    # breaking byte-for-byte parity with the original Node.js server. Disabling
    # it lets the catch-all route in ``app.main.routes`` handle every path and
    # every HTTP method uniformly.
    app = Flask(__name__, static_folder=None)

    # Load configuration from the Config object. Flask copies only the UPPERCASE
    # attributes (HOST, PORT, RESPONSE_BODY, CONTENT_TYPE), making them available
    # at request time via ``current_app.config[...]`` — which the route handler
    # relies on to reproduce the exact response body and Content-Type.
    app.config.from_object(Config)

    # Register the single ``main`` blueprint. Its catch-all route matches every
    # path and every HTTP method, reproducing the Node server's behavior of
    # returning one fixed response for all requests. No other blueprint is
    # registered: the single flow is intentional.
    app.register_blueprint(main_bp)

    # Return the fully-configured application to the caller (entrypoint).
    return app
