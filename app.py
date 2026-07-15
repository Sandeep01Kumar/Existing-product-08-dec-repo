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

# Every standard verb, mirroring Node's method-agnostic single handler.
METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']


@app.route('/', defaults={'path': ''}, methods=METHODS)
@app.route('/<path:path>', methods=METHODS)
def catch_all(path):
    # content_type (not mimetype) avoids an appended '; charset=utf-8',
    # preserving the exact header and the 14-byte body (incl. trailing \n).
    return Response('Hello, World!\n', status=200, content_type='text/plain')


if __name__ == '__main__':
    print(f'Server running at http://{HOST}:{PORT}/')
    app.run(host=HOST, port=PORT)
