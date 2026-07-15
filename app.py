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

# --- Bounded HTTP-parser parity residuals (AAP 0.6; NO code required) ---
# Node's original does no request validation in application code: its 400s
# for malformed requests come from the runtime HTTP parser (llhttp), not
# server.js. Werkzeug's dev-server parser diverges from llhttp on a few
# NON-CONFORMING inputs: a raw non-ASCII request target or a missing Host on
# HTTP/1.1 reach the catch-all (200 here) where Node answers 400; and a
# garbage request line, a bogus HTTP version, or an over-long URI are
# rejected by http.server with its own generic 400/414/505 page BEFORE WSGI
# dispatch (leaking nothing -- with debug=False there is no traceback/PIN/
# path) instead of reaching routing. These are framework/runtime differences,
# not app behavior, and are unreachable by conforming clients -- every
# conforming request stays exact byte-for-byte parity with Node (the AAP
# "no 404/500 page" guarantee holds at the application layer: everything that
# reaches routing returns the constant 200 Hello). Per AAP 0.7.1 ("no error
# handling may be added") and this module's spec ("Do NOT add error handlers/
# 404/500 pages"), the residuals are accepted as-is: adding a request-
# validator or error handler to mask them is prohibited (such a handler was
# reverted as review finding M-1) and could not restore full parity anyway.
# (CONNECT is a related residual -- see the METHODS note above.)


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
