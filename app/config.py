"""Application configuration for the Flask rewrite of the Node.js server.

Applies the Configuration Object pattern: the values hardcoded inline in the
original ``server.js`` are centralized here and preserved exactly, so the
rewrite reproduces the source's observable behavior byte-for-byte. This module
imports nothing and is the leaf of the ``app`` package import graph.
"""


class Config:
    """Constants ported verbatim from ``server.js``.

    Loaded via ``app.config.from_object(Config)``; only the UPPERCASE attributes
    below are copied into ``app.config``. Values must not change.
    """

    # Network binding (server.js L3-L4). PORT is an int and overrides Flask's
    # default development port (5000) so the rewrite binds 127.0.0.1:3000.
    HOST = '127.0.0.1'
    PORT = 3000

    # Fixed response contract (server.js L8-L9). RESPONSE_BODY keeps its trailing
    # newline (exactly 14 bytes -> Content-Length: 14). CONTENT_TYPE is exactly
    # 'text/plain' with NO charset: it is passed to Response(content_type=...)
    # verbatim, whereas Flask's mimetype= would append '; charset=utf-8'.
    RESPONSE_BODY = 'Hello, World!\n'
    CONTENT_TYPE = 'text/plain'
