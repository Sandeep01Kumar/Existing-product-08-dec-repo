"""Production WSGI entrypoint for the Flask rewrite of the Node.js server.

This module exposes the WSGI application callable under the well-known name
``app`` so a production WSGI server can import and serve it as ``wsgi:app``:

* gunicorn (UNIX, primary)::

      gunicorn --no-control-socket --bind 127.0.0.1:3000 wsgi:app

* waitress (cross-platform alternative)::

      waitress-serve --listen=127.0.0.1:3000 wsgi:app

Both bind the same ``127.0.0.1:3000`` interface as the source Node server
(``server.js`` L3-L4), preserving network parity while satisfying the
"performance not impacted" requirement of user rule "Ajit_New Product" by
serving the app through a production WSGI server rather than Flask's
development server.

``--no-control-socket`` is required on the gunicorn command. gunicorn 26
otherwise opens a Unix control socket (default ``$HOME/.gunicorn/gunicorn.ctl``)
backed by a management thread for runtime worker control -- an unplanned
management plane plus on-disk state, contrary to this fixture's isolation
(AAP 0.1.1, 0.7.1: no monitoring/management service). Disabling it removes the
socket, the thread, and the directory with no change whatsoever to the HTTP
response.

Production parity scope (AAP 0.6). For every path and every standard HTTP
method, both servers return -- through the shared application factory -- the
exact application-layer contract: status ``200``, header
``Content-Type: text/plain`` (no charset), and the body ``Hello, World!`` with a
trailing newline (14 bytes, hence ``Content-Length: 14`` on GET). That contract
is defined and enforced inside the ``app`` package (:mod:`app.main.routes`) and
is byte-for-byte identical whether served by the development server, gunicorn,
or waitress.

Per AAP 0.6, transport-layer traits that the WSGI server owns below the
application boundary are framework defaults -- not application logic -- and, like
Node's own ``Server`` / ``Date`` / ``Connection`` headers, lie outside the parity
contract:

* Response framing: the ``Server`` / ``Date`` / ``Connection`` headers, and on
  waitress a ``Transfer-Encoding: chunked`` on the bodyless HEAD response. The
  app deliberately omits ``Content-Length`` on HEAD to match Node; waitress then
  frames that response with chunking, while gunicorn frames it without.
* Request-body handling: waitress buffers the request body before invoking the
  application, whereas the app -- like the Node source -- ignores the request
  entirely, so the response content is unaffected.
* Method-token parsing: gunicorn and waitress reject malformed or lowercase
  method tokens at the parser, before WSGI dispatch. This transport/parser edge
  behavior is explicitly outside the AAP 0.6 parity scope (which is defined over
  paths and the standard methods) -- the same boundary documented in
  :mod:`app.main.routes`.

gunicorn (the UNIX primary) most closely matches the source's transport framing;
waitress is the cross-platform fallback for hosts where gunicorn is unavailable.

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
