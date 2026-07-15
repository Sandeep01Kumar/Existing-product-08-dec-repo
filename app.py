"""app.py - Python 3 / Flask port of the original Node.js server (``server.js``).

This module is a behavior-for-behavior re-implementation of the 14-line Node.js
HTTP server that previously lived in ``server.js``. It is the new entry point for
the project: run it with ``python app.py`` (this replaces ``node server.js``).

Overriding requirement (AAP sections 0.1, 0.6, 0.7.1): **behavioral parity**.
Every HTTP client must observe byte-for-byte identical results to the original
Node.js implementation. No features, configuration, endpoints, logging, auth,
persistence, or error pages are added beyond what ``server.js`` exhibited.

Original source being ported (``server.js``)::

    const http = require('http');
    const hostname = '127.0.0.1';
    const port = 3000;
    const server = http.createServer((req, res) => {
      res.statusCode = 200;
      res.setHeader('Content-Type', 'text/plain');
      res.end('Hello, World!\\n');
    });
    server.listen(port, hostname, () => {
      console.log(`Server running at http://${hostname}:${port}/`);
    });

Node -> Flask construct mapping (AAP section 0.1.2):

* ``require('http')``                       -> ``from flask import Flask, Response``
* ``http.createServer(handler)``            -> ``Flask(__name__, static_folder=None)``
* single method/path-agnostic handler       -> two routes (``/`` with defaults + ``/<path:path>``)
* ``res.statusCode = 200``                  -> ``Response(..., status=200)``
* ``res.setHeader('Content-Type', ...)``    -> ``content_type='text/plain'``
* ``res.end('Hello, World!\\n')``            -> ``Response('Hello, World!\\n', ...)``
* ``server.listen(3000, '127.0.0.1', cb)``  -> ``app.run(host=HOST, port=PORT)``
* ``console.log(...)``                      -> ``print(...)``

Documented, harmless residual differences (AAP section 0.6): the Werkzeug
development server adds a ``Server:`` header and prints its own startup banner,
and truly non-standard HTTP verbs (e.g. ``FOO``) may receive ``405``/``501``
instead of ``200``. These are the only bounded parity gaps and require no code.
"""

from flask import Flask, Response

# ---------------------------------------------------------------------------
# Module constants - mirror the source literals exactly (server.js lines 3-4).
# ---------------------------------------------------------------------------
# Loopback-only bind address. This intentionally mirrors ``const hostname``
# from server.js. It must NOT be broadened to '0.0.0.0' and must NOT be read
# from an environment variable - the original hardcoded it (AAP section 0.6 #11).
HOST = '127.0.0.1'

# Fixed listen port. Mirrors ``const port = 3000`` from server.js. Flask's own
# ``flask run`` default is 5000; we force 3000 to preserve the network contract
# (AAP section 0.6 #10). Hardcoded - no PORT env override (AAP section 0.6 #11).
PORT = 3000

# ---------------------------------------------------------------------------
# Application object (server.js line 6: http.createServer(...)).
# ---------------------------------------------------------------------------
# ``static_folder=None`` is REQUIRED (AAP section 0.6 #2): it disables Flask's
# default ``/static/<path:filename>`` route so that requests to /static/* fall
# through to the catch-all below and return the same 200 "Hello, World!\n"
# response instead of a 404. The ``app`` object is exposed at module level so it
# can also serve as the WSGI application for an optional production server later.
app = Flask(__name__, static_folder=None)


# ---------------------------------------------------------------------------
# Catch-all routing (server.js lines 6-10: single method/path-agnostic handler).
# ---------------------------------------------------------------------------
# Two route registrations on one view reproduce Node's handler that ignored the
# request entirely and answered every method + every path identically:
#   * ``/`` with ``defaults={'path': ''}`` handles the root exactly.
#   * ``/<path:path>`` handles every other path (the ``path`` converter also
#     matches embedded slashes, so arbitrarily deep paths are covered).
# ``methods`` enumerates every standard verb (AAP section 0.6 #1, #7). OPTIONS is
# listed explicitly so Flask routes it to this view (returning the Hello body)
# rather than short-circuiting with an automatic empty 200. HEAD is served by
# Werkzeug, which auto-strips the body - the client-observable result is
# identical to Node's low-level http behavior.
@app.route('/', defaults={'path': ''},
           methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
@app.route('/<path:path>',
           methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
def catch_all(path):
    """Return the constant plain-text greeting for any method and any path.

    The ``path`` parameter is accepted and deliberately ignored, mirroring the
    Node.js handler that ignored ``req`` and always produced the same response
    (server.js lines 6-10).

    The response reproduces the source contract exactly (server.js lines 7-9):

    * status ``200`` (server.js line 7: ``res.statusCode = 200``);
    * header ``Content-Type: text/plain`` with NO charset suffix - we pass
      ``content_type='text/plain'`` rather than ``mimetype='text/plain'``,
      because ``mimetype`` would append ``; charset=utf-8`` and break header
      parity (AAP section 0.6 #3);
    * body exactly ``'Hello, World!\\n'`` - 14 bytes including the trailing
      newline, yielding ``Content-Length: 14`` (AAP section 0.6 #4). The
      trailing newline is significant and must not be stripped or duplicated.
    """
    return Response('Hello, World!\n', status=200, content_type='text/plain')


# ---------------------------------------------------------------------------
# Entry point (server.js lines 12-13: server.listen + console.log callback).
# ---------------------------------------------------------------------------
# The ``if __name__ == '__main__':`` guard reproduces the direct-execution
# semantics of ``node server.js``: the server only starts when the module is run
# as a script, not when it is imported (e.g. by a WSGI host or a test).
if __name__ == '__main__':
    # Emit the identical startup line BEFORE binding, matching server.js line 13:
    #   "Server running at http://127.0.0.1:3000/"
    # Flask/Werkzeug additionally prints its own banner/dev-server warning; that
    # extra stdout is an accepted, harmless residual difference (AAP section 0.6 #10).
    print(f'Server running at http://{HOST}:{PORT}/')

    # Bind and serve. ``debug=False`` (the default) is intentional: no reloader
    # subprocess and no interactive debugger, matching the single-process startup
    # of ``node server.js`` (AAP section 0.6 #9). ``threaded`` is left at its
    # default; the AAP marks it optional and behaviorally harmless.
    app.run(host=HOST, port=PORT)
