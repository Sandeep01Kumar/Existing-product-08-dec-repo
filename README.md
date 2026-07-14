# hao-backprop-test

Test project for backprop integration.

This is a Python 3 [Flask](https://flask.palletsprojects.com/) application. For
every request path, and for each of the eight standard HTTP methods — `GET`,
`HEAD`, `POST`, `PUT`, `DELETE`, `PATCH`, `OPTIONS`, and `TRACE` — it returns
the same fixed response at the application layer: HTTP `200`, header
`Content-Type: text/plain`, and the body `Hello, World!` followed by a newline,
served on `http://127.0.0.1:3000/`. This reproduces the application-layer
behavior of the original Node.js server.

Parity is defined at the application layer, over request paths and the eight
standard methods listed above. Behavior for method tokens and connection types
that the HTTP server handles below the application — before a request reaches
Flask — is outside this guarantee and can differ both from the original Node
server and between the development server (Werkzeug) and the production servers
(gunicorn / waitress):

- `CONNECT`: a tunneling method handled at the transport layer rather than as a
  normal application request.
- Malformed, lowercase, or otherwise non-standard method tokens (for example
  `get` or `FOO`): gunicorn and waitress reject these at their HTTP parser, and
  the original Node server answered some of them with `400`.

## Setup

Requires Python 3.10 or later (gunicorn 26.0.0 requires Python 3.10+); Python
3.12 is the target runtime. Create a virtual environment:

```bash
python -m venv .venv
```

Activate it using the command for your shell:

- macOS / Linux (bash, zsh):

  ```bash
  source .venv/bin/activate
  ```

- Windows (cmd.exe):

  ```bat
  .venv\Scripts\activate.bat
  ```

- Windows (PowerShell):

  ```powershell
  .venv\Scripts\Activate.ps1
  ```

Then install the dependencies:

```bash
pip install -r requirements.txt
```

## Run

### Development (parity entrypoint)

Mirrors the original `node server.js`. It prints
`Server running at http://127.0.0.1:3000/` and listens on `127.0.0.1:3000`.

```bash
python server.py
```

### Production (UNIX — gunicorn)

Serves the WSGI application exposed as `app` in `wsgi.py`. The
`--no-control-socket` flag keeps the process isolated, with no gunicorn control
socket or management thread:

```bash
gunicorn --no-control-socket --bind 127.0.0.1:3000 wsgi:app
```

### Production (cross-platform — waitress)

```bash
waitress-serve --listen=127.0.0.1:3000 wsgi:app
```

## Verify

With the server running, every path and each of the eight standard HTTP methods
returns the same response:

```bash
curl http://127.0.0.1:3000/                  # -> Hello, World!
curl -X POST http://127.0.0.1:3000/any/path  # -> Hello, World!
```
