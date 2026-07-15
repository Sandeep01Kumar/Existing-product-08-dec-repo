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


@app.route('/', defaults={'path': ''}, methods=METHODS)
@app.route('/<path:path>', methods=METHODS)
def catch_all(path):
    # The single, constant response this app ever returns, mirroring Node's
    # res.end('Hello, World!\n'). content_type (not mimetype) avoids an
    # appended '; charset=utf-8', preserving the exact header and the 14-byte
    # body (incl. the trailing '\n'). The path arg is accepted and ignored,
    # mirroring Node's request-agnostic single handler.
    return Response('Hello, World!\n', status=200, content_type='text/plain')


if __name__ == '__main__':
    print(f'Server running at http://{HOST}:{PORT}/')
    # Explicit debug=False keeps the reloader and interactive debugger off even
    # when FLASK_DEBUG=1 is set in the environment (an explicit value passed
    # to app.run overrides the FLASK_DEBUG env var). This preserves the
    # single-process startup of `node server.js` and closes the latent
    # debugger/RCE surface.
    app.run(host=HOST, port=PORT, debug=False)
