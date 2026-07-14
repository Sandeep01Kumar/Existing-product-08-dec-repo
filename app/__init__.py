"""Application package: the Application Factory for the Flask rewrite.

``create_app()`` is the structural replacement for the source
``http.createServer`` bootstrap (server.js L6): rather than a module-level
global server, it builds and configures a fresh Flask app on demand -- loading
``Config`` and registering the ``main`` blueprint whose catch-all route
reproduces the Node server's universal request handler. The factory performs no
I/O and starts no server; process startup lives in ``server.py`` / ``wsgi.py``.
"""

from flask import Flask

from app.config import Config
from app.main import main_bp


def create_app():
    """Create and configure the Flask application (Application Factory).

    Returns a fully-configured :class:`flask.Flask` instance, safe to run via
    ``server.py`` (development/parity) or serve as ``wsgi:app`` (production).
    """
    # static_folder=None disables Flask's automatic '/static/<path:filename>'
    # route at construction -- a supported Flask constructor option, so no
    # manual URL-map surgery is needed. The source serves no static assets and
    # returns the SAME response for EVERY path, so the main blueprint's
    # catch-all must own '/static/...' too; otherwise the default static route
    # would answer e.g. 'OPTIONS /static/...' with Flask's automatic (empty)
    # response instead of the universal body. Disabling static at construction
    # also leaves has_static_folder False and static_folder None (no orphaned
    # 'static' endpoint), keeping the URL map limited to the blueprint's two
    # rules.
    app = Flask(__name__, static_folder=None)

    # Copy Config's UPPERCASE attributes (HOST, PORT, RESPONSE_BODY,
    # CONTENT_TYPE) into app.config for the route handler to read at request time.
    app.config.from_object(Config)

    # Register the single blueprint; its catch-all matches every path and method.
    app.register_blueprint(main_bp)

    return app
