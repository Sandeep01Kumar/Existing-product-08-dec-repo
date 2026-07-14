"""Catch-all route: the Flask reproduction of the Node.js universal handler.

The source ``http.createServer`` callback (server.js L6-L10) ran for every
request, ignored it entirely, and always replied 200 / ``text/plain`` /
``Hello, World!\n``. This module reproduces that contract on Flask.

Method coverage & parity scope (accurate as of this implementation):

* The two catch-all rules bind the eight standard methods in ``METHODS`` (GET,
  HEAD, POST, PUT, DELETE, PATCH, OPTIONS, TRACE); those reach ``catch_all``
  directly.
* Any OTHER method the WSGI server forwards -- extension methods (e.g.
  PROPFIND, M-SEARCH), the CONNECT method, or non-standard tokens -- does not
  match the bound method set, so Werkzeug raises 405 and ``catch_all_errors``
  maps it back to the same 200 response. An unmatched path (404) is handled the
  same way. These fallbacks are what make the response universal; the explicit
  list alone does not cover "every HTTP method". This is the AAP 0.6
  belt-and-suspenders design and yields the "one response for every path and
  every method" contract (AAP 0.1.1).
* This intentionally does NOT reproduce Node's transport/parser-level edge
  behavior -- e.g. llhttp answering an unknown method token with 400, or an
  unhandled CONNECT being closed via a separate socket event. Those live below
  the WSGI boundary, are not portably expressible in a Flask/WSGI app, and
  would contradict the AAP's universal-response contract (AAP 0.1.1); they fall
  outside the AAP 0.6 parity scope, which was defined over paths and the eight
  standard methods.
"""

from flask import Response, current_app, request

from app.main import main_bp

# Standard methods bound explicitly so they reach the handler directly. Methods
# outside this list still return the identical response via the 404/405
# fallback below (see the module docstring's "Method coverage" note).
METHODS = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'TRACE']


@main_bp.route('/', defaults={'path': ''}, methods=METHODS,
               strict_slashes=False, provide_automatic_options=False)
@main_bp.route('/<path:path>', methods=METHODS,
               strict_slashes=False, provide_automatic_options=False)
def catch_all(path):
    """Return the fixed 200 / ``text/plain`` / ``Hello, World!\n`` for any request.

    Rule flags (parity-critical): ``defaults={'path': ''}`` lets the root reuse
    this view; ``<path:path>`` matches slash-containing paths; and
    ``strict_slashes=False`` disables Werkzeug's 308 trailing-slash redirects
    (Node issued none). ``provide_automatic_options=False`` lets OPTIONS reach
    this view instead of Flask's automatic ``Allow`` response, so OPTIONS
    returns the identical body. ``content_type=`` sets the header verbatim
    (``mimetype=`` would append ``; charset=utf-8``). ``path`` is unused: the
    response is unconditional, mirroring the source callback ignoring ``req``.
    """
    return Response(
        current_app.config['RESPONSE_BODY'],
        status=200,
        content_type=current_app.config['CONTENT_TYPE'],
    )


@main_bp.app_errorhandler(404)
@main_bp.app_errorhandler(405)
def catch_all_errors(error):
    """Map any 404/405 to the identical 200 response (AAP 0.6 fallback).

    This is the mechanism by which methods outside ``METHODS`` (extension
    methods, CONNECT, non-standard tokens) and any unmatched path still receive
    the universal response. The ``error`` argument is intentionally unused.
    """
    return Response(
        current_app.config['RESPONSE_BODY'],
        status=200,
        content_type=current_app.config['CONTENT_TYPE'],
    )


@main_bp.after_app_request
def omit_content_length_on_head(response):
    """Match the Node server's HEAD response, which omits ``Content-Length``.

    Werkzeug derives HEAD from GET and would emit ``Content-Length: 14``; the
    Node source sends none. Popping the header is not sufficient -- Werkzeug
    re-adds it at WSGI emission unless ``automatically_set_content_length`` is
    also disabled. Status 200, the exact ``text/plain`` Content-Type, and the
    empty HEAD body are left unchanged.
    """
    if request.method == 'HEAD':
        response.headers.pop('Content-Length', None)
        response.automatically_set_content_length = False
    return response
