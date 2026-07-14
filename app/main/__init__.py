"""The ``main`` blueprint: the application's sole request-handling flow.

This module is pure modular scaffolding for the Flask rewrite of the original
Node.js server. It defines the :class:`~flask.Blueprint` object that carries
the application's single, universal request-handling flow and, at the bottom of
the module, performs a deferred import of the routes module so that importing
``main_bp`` also registers the catch-all route on the blueprint.

The deferred import at the end of the file breaks the circular dependency
between this module (which defines ``main_bp``) and :mod:`app.main.routes`
(which imports ``main_bp`` from here). The parent application factory in
``app/__init__.py`` consumes this module via ``from app.main import main_bp``
followed by ``app.register_blueprint(main_bp)``.

This file intentionally contains no request-handling logic, routes, error
handlers, or configuration; those responsibilities live in
:mod:`app.main.routes` and :mod:`app.config` respectively.
"""

from flask import Blueprint

# The ``main`` blueprint encapsulates the application's sole request-handling
# flow. The name string ``'main'`` and the variable name ``main_bp`` form the
# public contract relied upon by the parent application factory; neither may be
# renamed. No ``url_prefix`` is supplied so the catch-all route registered in
# ``app.main.routes`` matches every path from the application root.
main_bp = Blueprint('main', __name__)

# Deferred (bottom-of-module) import performed for its side effect: importing
# ``app.main.routes`` registers the catch-all route on ``main_bp`` above. It is
# placed here -- after ``main_bp`` is defined -- to break the circular import
# between this module and ``app.main.routes`` (which imports ``main_bp`` from
# this module). Importing it at the top of the file would raise an ImportError.
# ``# noqa: E402,F401`` suppresses the expected "module level import not at top
# of file" (E402) and "imported but unused" (F401) lint warnings; the import is
# intentional and its side effect (route registration) is the reason it exists.
from app.main import routes  # noqa: E402,F401
