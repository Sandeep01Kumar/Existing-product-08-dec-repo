"""The ``main`` blueprint: the application's sole request-handling flow.

Defines the blueprint object and, at the bottom of the module, performs a
deferred import of the routes module so that importing ``main_bp`` also
registers the catch-all route. The name ``'main'`` and the variable ``main_bp``
are the public contract the application factory relies on.
"""

from flask import Blueprint

main_bp = Blueprint('main', __name__)

# Deferred (bottom-of-module) import, run for its side effect: importing
# ``app.main.routes`` registers the catch-all route on ``main_bp``. It must come
# after ``main_bp`` is defined -- importing at the top would create a circular
# import, since routes.py imports ``main_bp`` from here. ``# noqa: E402,F401``
# suppresses the resulting (expected) "import not at top" / "unused" warnings.
from app.main import routes  # noqa: E402,F401
