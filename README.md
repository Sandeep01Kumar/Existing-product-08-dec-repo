# hao-backprop-test

Test project for backprop integration.

This is a Python 3 [Flask](https://flask.palletsprojects.com/) application. For
every request path and every HTTP method it returns the same fixed response —
HTTP `200`, header `Content-Type: text/plain`, and the body `Hello, World!`
followed by a newline — served on `http://127.0.0.1:3000/`. This reproduces the
behavior of the original Node.js server exactly.

## Setup

Requires Python 3. Create and activate a virtual environment, then install the
dependencies:

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
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

With the server running, every path and method returns the same response:

```bash
curl http://127.0.0.1:3000/    # -> Hello, World!
```
