"""Catch-all route: the Flask reproduction of the Node.js universal handler.

This module ports the single request-handling flow of the original Node.js
server (``server.js`` L6-L10) to Flask, preserving its observable behavior
**byte-for-byte**. The original ``http.createServer`` callback ran for *every*
request and ignored the request object entirely, always replying with::

    HTTP/1.1 200 OK
    Content-Type: text/plain
    Content-Length: 14

    Hello, World!\\n

To reproduce that "one response for everything" contract on top of Flask's
route-matching engine, this module registers a pair of *catch-all* rules on the
``main`` blueprint (see :mod:`app.main`). Together they match every path, and
the explicit ``methods`` list makes them match every HTTP method, so Flask never
produces a ``404`` (no matching route), ``405`` (method not allowed), or ``308``
(trailing-slash redirect) -- none of which the Node server ever emitted.

Design notes / parity rationale:

* **Configuration, not literals.** The response body and ``Content-Type`` are
  read from ``current_app.config`` (keys ``RESPONSE_BODY`` and ``CONTENT_TYPE``,
  populated by ``create_app()`` via ``app.config.from_object(Config)`` from
  :mod:`app.config`). This keeps every ported constant traceable to a single
  source of truth. The HTTP status ``200`` is passed as a literal because it is
  a universal HTTP constant, mirroring the source, which set ``res.statusCode``
  inline in the callback.
* **``content_type=`` (not ``mimetype=``).** The response is constructed with
  the ``content_type`` argument so the header is emitted *verbatim* as
  ``text/plain``. Flask's ``mimetype`` argument would cause Werkzeug to append
  ``; charset=utf-8`` for text mimetypes -- something the Node server never sent
  and which would break byte-for-byte parity.
* **The request is ignored.** Like the source callback that never inspected
  ``req``, the view reads nothing from the incoming request (no body, query
  string, or headers) and branches on nothing; the response is unconditional.

Import graph (AAP 0.4.2)::

    app/main/__init__.py --(deferred import)-->     app/main/routes.py
    app/main/routes.py    --imports-->              main_bp (from app.main)
    app/main/routes.py    --reads at request time-->  current_app.config (app.config)
"""

from flask import Response, current_app

from app.main import main_bp

# Every standard HTTP method is listed explicitly so that the catch-all rules
# accept them all and Werkzeug never raises ``405 Method Not Allowed``. This
# mirrors the Node server, whose single callback fired regardless of method.
#   * ``HEAD`` is auto-derived from ``GET`` by Werkzeug (the body is stripped
#     per the HTTP spec); listing it explicitly is harmless and documents intent.
#   * ``OPTIONS`` and ``TRACE`` are included so those methods reach this handler
#     too, rather than being intercepted by any framework default.
METHODS = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'TRACE']


@main_bp.route('/', defaults={'path': ''}, methods=METHODS,
               strict_slashes=False, provide_automatic_options=False)
@main_bp.route('/<path:path>', methods=METHODS,
               strict_slashes=False, provide_automatic_options=False)
def catch_all(path):
    """Return the fixed response for *any* path and *any* HTTP method.

    Two rules are stacked on this single view function so that both the
    application root (``/``) and every sub-path (including slash-containing
    paths such as ``/any/random/path``) resolve here:

    * The root rule supplies ``defaults={'path': ''}`` so this view's required
      ``path`` parameter is satisfied when serving ``/``.
    * The sub-path rule uses the ``<path:path>`` converter which -- unlike the
      default string converter -- matches segments that contain slashes.

    Both rules set:

    * ``strict_slashes=False`` -- disables Werkzeug's automatic ``308`` redirect
      for trailing slashes (e.g. ``/foo/`` -> ``/foo``); the Node server never
      issued such redirects.
    * ``provide_automatic_options=False`` -- stops Flask from short-circuiting
      ``OPTIONS`` requests with an automatic ``Allow``-header response, so this
      handler runs for ``OPTIONS`` and returns the identical body, matching Node.

    The ``path`` argument is intentionally unused: the response is unconditional,
    faithfully reproducing the source callback that ignored ``req`` entirely.
    """
    return Response(
        current_app.config['RESPONSE_BODY'],
        status=200,
        content_type=current_app.config['CONTENT_TYPE'],
    )


@main_bp.app_errorhandler(404)
@main_bp.app_errorhandler(405)
def catch_all_errors(error):
    """Defensive fallback so that no ``404``/``405`` can ever escape.

    The catch-all rules above already make ``404`` (no matching route) and
    ``405`` (method not allowed) unreachable in normal operation. These
    application-wide handlers -- registered via the blueprint -- are a
    belt-and-suspenders guarantee (endorsed by AAP 0.6): should any request ever
    fail to match, it still receives the exact same ``200`` / ``text/plain`` /
    ``Hello, World!\\n`` response, preserving parity with the Node server.

    The ``error`` argument (the raised ``HTTPException``) is intentionally
    unused; the response is unconditional.
    """
    return Response(
        current_app.config['RESPONSE_BODY'],
        status=200,
        content_type=current_app.config['CONTENT_TYPE'],
    )
