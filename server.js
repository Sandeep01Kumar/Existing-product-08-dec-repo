const express = require('express');

const hostname = '127.0.0.1';
const port = 3000;

// Instantiate the Express application. Express manages the underlying HTTP
// server internally, replacing the previous http.createServer() bootstrap.
const app = express();

// GET / — greeting endpoint (backward compatible with the original server).
// Returns the exact body 'Hello, World!\n' as text/plain with HTTP 200
// (200 is Express's default status for res.send()).
app.get('/', (req, res) => {
  res.type('text/plain').send('Hello, World!\n');
});

// GET /good-evening — second endpoint returning the exact body 'Good evening'
// as text/plain with HTTP 200.
app.get('/good-evening', (req, res) => {
  res.type('text/plain').send('Good evening');
});

// Start the server, preserving the original 127.0.0.1:3000 binding and the
// startup log message. Capture the returned server so startup/bind failures can
// be observed instead of being silently misreported as a successful start.
const server = app.listen(port, hostname, () => {
  // Express 5 registers this callback as a one-time 'error' listener in addition
  // to the 'listening' event, so it is invoked on a failed bind too (with the
  // socket not actually listening). Announce success only once the socket is
  // genuinely bound to avoid emitting a false "running" signal.
  if (server.listening) {
    console.log(`Server running at http://${hostname}:${port}/`);
  }
});

// Report startup/bind errors (e.g. EADDRINUSE when the port is already in use)
// on stderr and exit with a non-zero status so operators, scripts, health
// checks, and orchestration receive an accurate failure signal instead of a
// false success.
server.on('error', (err) => {
  console.error(`Failed to start server at http://${hostname}:${port}/: ${err.message}`);
  process.exit(1);
});
