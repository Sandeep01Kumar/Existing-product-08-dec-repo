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
    app = Flask(__name__)

    # Flask(__name__) auto-registers a '/static/<path:filename>' route. The
    # source serves no static assets and returns the SAME response for EVERY
    # path, so that route is removed before the blueprint is registered -- the
    # catch-all then handles '/static/...' too. This matters for parity beyond
    # 404s: the default static route would answer 'OPTIONS /static/...' with
    # Flask's automatic (empty) response instead of the universal body. Werkzeug
    # exposes no rule-removal API, so we swap in a fresh url_map (same config)
    # and drop the orphaned 'static' view -- both public-API operations.
    app.url_map = app.url_map_class(host_matching=app.url_map.host_matching)
    app.view_functions.pop('static', None)

    # Copy Config's UPPERCASE attributes (HOST, PORT, RESPONSE_BODY,
    # CONTENT_TYPE) into app.config for the route handler to read at request time.
    app.config.from_object(Config)

    # Register the single blueprint; its catch-all matches every path and method.
    app.register_blueprint(main_bp)

    return app
