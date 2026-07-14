"""Production WSGI entrypoint for the Flask rewrite of the Node.js server.

This module exposes the WSGI application callable under the well-known name
``app`` so a production WSGI server can import and serve it as ``wsgi:app``:

* gunicorn (UNIX)::

      gunicorn --bind 127.0.0.1:3000 wsgi:app

* waitress (cross-platform)::

      waitress-serve --listen=127.0.0.1:3000 wsgi:app

Both bind the same ``127.0.0.1:3000`` interface as the source Node server
(``server.js`` L3-L4), preserving network parity while satisfying the
"performance not impacted" requirement of user rule "Ajit_New Product" by
serving the app through a production WSGI server rather than Flask's
development server.

The application object is built once, at import time, via the Application
Factory :func:`app.create_app`. ``create_app()`` opens no socket and starts no
server, so importing this module is side-effect free -- the WSGI server drives
the request/response loop. Deliberately, this module contains no ``app.run(...)``
call and no ``if __name__ == "__main__"`` guard: starting Flask's development
server is the sole responsibility of the development/parity entrypoint
``server.py`` (which also emits the exact Node-style startup log line). Request
handling, the response contract, and the network constants all live inside the
``app`` package (:mod:`app.main.routes` and :class:`app.config.Config`); this
entrypoint only wires the factory output to the WSGI boundary.
"""

from app import create_app

# Module-level WSGI callable. Named exactly ``app`` (lowercase) so the
# ``wsgi:app`` reference used by gunicorn/waitress resolves. Built eagerly at
# import so the production server has an application ready to serve on load;
# create_app() performs no I/O, keeping this import side-effect free.
app = create_app()
