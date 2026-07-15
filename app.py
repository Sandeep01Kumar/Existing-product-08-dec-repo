"""Flask port of the Node.js server (server.js), preserving its behavior.

Every method and path returns 200, Content-Type text/plain, and the body
'Hello, World!' plus a trailing newline. Run with `python app.py`.
"""

from flask import Flask, Response

HOST = '127.0.0.1'
PORT = 3000

# static_folder=None disables Flask's default /static route so /static/*
# also falls through to the catch-all below (matches the Node handler).
app = Flask(__name__, static_folder=None)

# Every standard HTTP verb (RFC 9110), mirroring Node's method-agnostic single
# handler. TRACE is included so it is routed to the view and answers with the
# same 200 response as Node (Node's low-level handler serves the body for TRACE
# too); without it Werkzeug rejects TRACE with 405, breaking parity.
# CONNECT is intentionally omitted: Node's http server special-cases it and
# drops the connection (no HTTP response), so it never serves the Hello body --
# enumerating it here would create a *new* divergence instead of parity.
METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD', 'TRACE']


def _hello_response():
    """Build the single, constant HTTP response this app ever returns.

    Reused by both the catch-all view and the 404 handler so the two response
    sites can never drift. content_type (not mimetype) avoids an appended
    '; charset=utf-8', preserving the exact header and the 14-byte body
    (incl. the trailing '\n').
    """
    return Response('Hello, World!\n', status=200, content_type='text/plain')


@app.route('/', defaults={'path': ''}, methods=METHODS)
@app.route('/<path:path>', methods=METHODS)
def catch_all(path):
    return _hello_response()


@app.errorhandler(404)
def catch_all_404(error):
    # Werkzeug's URL router rejects a decoded newline in the path (e.g. %0a or
    # %0d%0a) with a 404 *before* the catch-all view runs. Node's path-agnostic
    # handler ignores the path entirely and still answers 200, so we convert
    # that 404 back into the identical constant response. This preserves
    # byte-for-byte parity and honours the contract that no 404/500 page
    # is ever produced (AAP behavioral-parity requirement).
    return _hello_response()


if __name__ == '__main__':
    print(f'Server running at http://{HOST}:{PORT}/')
    # Explicit debug=False keeps the reloader and interactive debugger off even
    # when FLASK_DEBUG=1 is set in the environment (an explicit value passed
    # to app.run overrides the FLASK_DEBUG env var). This preserves the
    # single-process startup of `node server.js` and closes the latent
    # debugger/RCE surface.
    app.run(host=HOST, port=PORT, debug=False)
