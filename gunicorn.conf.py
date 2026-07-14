"""Gunicorn configuration for production serving of the Flask rewrite.

This file is the "explicitly sized concurrent Gunicorn configuration" that
satisfies the performance clause of user rule "Ajit_New Product" ("Ensure the
performance of the application is not impacted by this code") and the AAP's
designation of gunicorn as the mechanism that supports that rule
(AAP 0.3.3 WSGI application pattern, 0.5.1). Gunicorn auto-discovers a
``gunicorn.conf.py`` in the working directory; it is also loaded explicitly by
the documented command::

    gunicorn --no-control-socket -c gunicorn.conf.py wsgi:app

WHY THIS FILE EXISTS -- the problem it fixes
--------------------------------------------
Gunicorn's out-of-the-box defaults are a SINGLE synchronous worker
(``workers = 1``, ``worker_class = "sync"``, ``threads = 1``). With one sync
worker the server processes exactly one request at a time and reads each request
to completion before accepting the next. That has two consequences that break
the "performance not impacted" rule relative to the Node.js event-loop original:

* Head-of-line blocking / trivial DoS: a single slow or incomplete client
  (e.g. a Slowloris-style request that dribbles headers and never completes)
  occupies the lone worker for up to ``timeout`` seconds, during which EVERY
  other client is starved and times out. The Node source, being event-driven,
  never blocked this way.
* Throughput ceiling under concurrency: one worker cannot use more than a single
  CPU, so aggregate throughput collapses as concurrency rises.

The development/parity entrypoint (``server.py``) already avoids this by running
Werkzeug with ``threaded=True``; this file brings the SAME non-blocking,
concurrent behaviour to the production path.

HOW IT FIXES IT
---------------
* ``worker_class = "gthread"`` gives each worker a thread pool. Request reading
  and handling happen on a worker thread, so a slow/incomplete client ties up
  ONE thread, never the whole worker -- other requests continue on the remaining
  threads. This eliminates the head-of-line blocking above.
* Multiple ``workers`` add process-level parallelism and isolation: even if one
  worker's threads are momentarily saturated, the others keep serving, and work
  is spread across the available CPUs. Two or more workers are required to clear
  the incomplete-request-body blocking case; four workers clear the high-load
  throughput threshold.

The application contract is UNCHANGED: every path and standard method still
returns ``200`` / ``text/plain`` (no charset) / ``Hello, World!\n`` (14 bytes),
served on loopback ``127.0.0.1:3000`` exactly as the source Node server. Worker
and thread counts are a transport/serving concern below the application boundary
and do not alter a single response byte.
"""

import os

# --- Network binding -------------------------------------------------------
# Loopback-only, port 3000 -- byte-for-byte network parity with the Node source
# (server.js L3-L4), overriding Flask's development default of 5000. Kept
# overridable via GUNICORN_BIND purely so parallel test runs can pick a distinct
# port; the delivered default is the AAP-mandated 127.0.0.1:3000, and it never
# binds a wildcard/public interface.
bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:3000")

# --- Concurrency model -----------------------------------------------------
# Threaded workers: a thread pool per worker so a single slow/incomplete client
# cannot monopolise a worker (see the module docstring). gunicorn switches a
# worker to the threaded implementation automatically when worker_class is
# "gthread" (and whenever threads > 1).
worker_class = "gthread"

# Explicitly sized, FIXED defaults (NOT derived from CPU count on purpose):
# this container reports 128 logical CPUs (multiprocessing.cpu_count() and
# os.sched_getaffinity both return 128) while being cgroup-limited to ~4 CPUs,
# so a conventional ``2 * cpu + 1`` formula would spawn hundreds of workers and
# exhaust memory. A fixed, modest pool is correct for this minimal fixture:
# 4 workers x 4 threads = 16 concurrent request slots -- ample to keep the
# server responsive under the QA load profile while remaining lightweight.
# Both are overridable via environment variables for operators who want to tune
# for a specific host (WEB_CONCURRENCY is gunicorn's conventional worker knob).
workers = int(os.environ.get("GUNICORN_WORKERS") or os.environ.get("WEB_CONCURRENCY") or 4)
threads = int(os.environ.get("GUNICORN_THREADS") or 4)
