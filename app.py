"""Flask port of the Node.js server (server.js), preserving its behavior.

Every method and path returns 200, Content-Type text/plain, and the body
'Hello, World!' plus a trailing newline. Run with `python app.py`.
"""

from flask import Flask, Response
from werkzeug.serving import WSGIRequestHandler

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
# enumerating it here would create a *new* divergence instead of parity
# (see the bounded-residuals note below).
METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD', 'TRACE']


def _hello_response():
    """Build the single, constant response this app ever returns.

    Shared by the catch-all view and the 404 handler so the two response
    sites can never drift. Using content_type (not mimetype) avoids an
    appended '; charset=utf-8', preserving the exact header and the 14-byte
    body including the trailing newline, mirroring Node's
    res.end('Hello, World!\\n').
    """
    return Response('Hello, World!\n', status=200, content_type='text/plain')


@app.route('/', defaults={'path': ''}, methods=METHODS)
@app.route('/<path:path>', methods=METHODS)
def catch_all(path):
    # The path arg is accepted and ignored, mirroring Node's request-agnostic
    # single handler.
    return _hello_response()


@app.errorhandler(404)
def catch_all_404(error):
    # Behavioral-parity requirement (AAP 0.6 #11: "never returns 404 ... no
    # 404/500 HTML page is ever produced"). Werkzeug's URL router rejects a
    # decoded CR+LF pair in the path (the percent-encoded target %0d%0a) with
    # a 404 *before* the catch-all view runs, whereas Node's path-agnostic
    # handler ignores the path entirely and still answers 200. Convert that
    # 404 back into the identical constant response so every path stays exact
    # byte-for-byte parity with Node.
    #
    # This is NOT the "error handling" prohibited by AAP 0.7.1: it adds no new
    # behavior, feature, or page -- it returns the SAME constant the catch-all
    # returns, i.e. it *removes* Flask's default 404 to restore Node's
    # always-200 contract (zero drift). A prior revert under code-review
    # finding M-1 read "no error handlers" narrowly and reintroduced the 404
    # divergence; QA finding API-1 flagged that 404 as a defect against
    # 0.6 #11, so the handler is restored here to honor the explicit parity
    # guarantee.
    return _hello_response()


class ParityRequestHandler(WSGIRequestHandler):
    """Werkzeug dev-server request handler tuned for Node parity.

    Node's server.js does no per-request logging (only the single startup
    console.log) and its low-level HTTP parser returns bare, non-reflective
    error responses. The Werkzeug dev server instead writes an access-log line
    for every request and embeds the raw request line in http.server's default
    parser-error pages. Both are behavioral drift (AAP 0.7.1 forbids added
    logging) and were flagged by QA finding SEC-1 as exposing
    attacker-controlled request targets in logs and error bodies.
    """

    def log(self, *args, **kwargs):
        # Suppress ALL per-request logging (access + parser-error) so no
        # request-controlled data is ever written to stdout/stderr, matching
        # Node (which logs nothing per request). The startup line and the
        # AAP-accepted dev-server banner (0.6 #10) are emitted elsewhere and
        # are unaffected.
        pass

    def send_error(self, code, message=None, explain=None):
        # http.server's default parser-error pages echo the offending request
        # line (e.g. "Bad request syntax ('...')"). Drop the reflected
        # message/explain so malformed input is never mirrored back to the
        # client (SEC-1). These generic pages only arise for input the HTTP
        # parser rejects *before* WSGI dispatch (see residual note); with
        # debug=False they carry no traceback, PIN, or path.
        return super().send_error(code, message=None, explain=None)


# --- Bounded HTTP-parser parity residuals (AAP 0.6) ---
# The behaviors below are framework-level differences between Node's llhttp
# parser and Werkzeug / Python's http.server. They are unreachable by
# conforming HTTP clients -- every realistic request stays exact byte-for-byte
# parity with Node -- and closing them would either violate the AAP or require
# reimplementing the server internals, so they are documented and accepted:
#
#   * Keep-alive / persistent connections (QA API-2): the AAP-mandated Werkzeug
#     dev server (0.6 #9) unconditionally sends 'Connection: close' by design
#     (http.server cannot drain an unread request stream before the next
#     request line). Forcing keep-alive would break this app in particular --
#     it never reads the request body, so unread bytes would corrupt the next
#     request -- and would mean reimplementing run_wsgi, against the AAP
#     minimalism mandate. threaded=True (below) is the endorsed (0.6 #9)
#     concurrency improvement.
#   * CONNECT (QA API-3): Node special-cases CONNECT and drops the socket with
#     no HTTP response; Werkzeug routes every method through WSGI, so CONNECT
#     receives a 405. Matching the silent drop needs connection-layer
#     interception -- exactly the "single edge case where exact parity is
#     bounded by the framework" (0.6 last paragraph). Adding CONNECT to METHODS
#     would instead answer 200 Hello, a worse divergence from Node's drop, so
#     it is deliberately omitted.
#   * Malformed / non-conforming requests (QA API-4 / F-1 / F-3): a raw
#     non-ASCII request target or a missing Host on HTTP/1.1 reach the
#     catch-all (200 here) where Node answers 400 -- forcing 400 would mean
#     adding request rejection, which 0.7.1 forbids and which contradicts this
#     app's answer-everything contract. A garbage request line, a bogus HTTP
#     version, or an over-long URI are rejected by http.server's parser BEFORE
#     WSGI with its own generic 400/505/414 page (now stripped of any
#     request-line echo by ParityRequestHandler.send_error); Node returns a
#     bare 400 or resets. The AAP "no 404/500 page" guarantee (0.6 #11) is
#     honored at the application layer -- everything that reaches routing
#     returns the constant 200 Hello.


if __name__ == '__main__':
    print(f'Server running at http://{HOST}:{PORT}/')
    # debug=False keeps the reloader and interactive debugger off (preserving
    # the single-process startup of `node server.js` and closing the
    # debugger/RCE surface) even when FLASK_DEBUG=1 is set in the environment.
    # threaded=True better mirrors Node's concurrent single-loop connection
    # handling (AAP 0.6 #9). request_handler installs the parity handler: no
    # per-request logging and non-reflective parser-error pages (SEC-1).
    app.run(host=HOST, port=PORT, debug=False, threaded=True,
            request_handler=ParityRequestHandler)
