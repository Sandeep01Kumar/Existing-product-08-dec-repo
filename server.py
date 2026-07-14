"""Development / parity entrypoint for the Flask rewrite of the Node.js server.

This module is the Python counterpart of running ``node server.js``: it is the
process entrypoint that reproduces the *startup* behavior of the original
Node.js server's listener/log block (``server.js`` L12-L14)::

    server.listen(port, hostname, () => {
      console.log(`Server running at http://${hostname}:${port}/`);
    });

with ``hostname = '127.0.0.1'`` and ``port = 3000``.

Responsibilities (and only these):

* Build the application **once** via the Application Factory
  (:func:`app.create_app`) and expose it as a module-level ``app`` object.
* When executed directly (``python server.py``), print the exact startup banner
  the Node server emitted and then start Flask's built-in development/WSGI
  server bound to the same interface and port as the original.

What this module deliberately does **not** do: it contains no request-handling
logic. Every request is handled by the universal catch-all route in
:mod:`app.main.routes`, exactly reproducing the Node server's single
``http.createServer`` callback. The response contract (HTTP ``200``,
``Content-Type: text/plain`` with no charset, body ``Hello, World!\\n`` /
``Content-Length: 14``) is owned by that route and the centralized
:class:`app.config.Config`, not by this entrypoint.

Behavioral parity notes (AAP 0.6):

* **Host/port** are sourced from :class:`~app.config.Config` (``HOST`` /
  ``PORT``) so the server binds ``127.0.0.1:3000``. This explicitly overrides
  Flask's default development port of ``5000`` — the values are never left to
  defaults.
* **Startup line** is printed verbatim as ``Server running at
  http://127.0.0.1:3000/`` (trailing slash included), byte-for-byte identical to
  ``server.js`` L13. Flask's own development banner (e.g.
  ``* Running on http://127.0.0.1:3000``) is additionally emitted by
  ``app.run(...)``; that extra banner is acceptable and does not replace the
  required exact line above.
* **Import safety** — the print and ``app.run(...)`` calls live inside the
  ``if __name__ == "__main__":`` guard, so importing this module (for example by
  a test harness) constructs the app without opening a socket or blocking.
* **No debug / no reloader** — ``app.run`` is called without ``debug=True`` and
  without the auto-reloader, keeping the observable HTTP contract identical to
  the source and avoiding a second child process. Production serving is handled
  separately by the WSGI entrypoint (``wsgi.py``) under gunicorn / waitress.

Import graph (AAP 0.4.2)::

    server.py --imports--> app.create_app   (application factory)
    server.py --imports--> app.config.Config (HOST / PORT constants)
"""

# --- Explicit imports only (no star imports; AAP 0.5.2) ------------------------
# The Application Factory that constructs and configures the Flask instance.
# Defined in ``app/__init__.py``; importing it runs no network/startup side
# effects — it only makes the factory callable available here.
from app import create_app

# The centralized configuration object holding the network-binding constants
# (HOST, PORT) ported verbatim from ``server.js`` L3-L4. Used both to render the
# startup banner and to bind the development server below.
from app.config import Config

# Construct the application a single time at module import. Exposing ``app`` at
# module level (rather than only inside the ``__main__`` guard) mirrors the WSGI
# entrypoint's contract and keeps the module importable for testing without
# starting a server. ``create_app()`` performs no I/O and opens no socket, so
# this assignment is side-effect free.
app = create_app()


if __name__ == "__main__":
    # Emit the startup banner EXACTLY as the Node server did (``server.js`` L13).
    # With Config.HOST == '127.0.0.1' and Config.PORT == 3000 this f-string
    # renders precisely "Server running at http://127.0.0.1:3000/" (trailing
    # slash included), reproducing the original console line byte-for-byte. It is
    # printed BEFORE ``app.run(...)`` because ``app.run`` blocks in the server
    # loop and would otherwise never yield control back to print it.
    print(f"Server running at http://{Config.HOST}:{Config.PORT}/")

    # Start Flask's built-in server, binding the exact interface and port from
    # Config so the rewrite listens on 127.0.0.1:3000 like the Node original.
    # This explicitly overrides Flask's default port (5000). ``debug`` and the
    # auto-reloader are intentionally left at their defaults (off) to preserve
    # the exact observable HTTP contract and avoid spawning a reloader child.
    app.run(host=Config.HOST, port=Config.PORT)
