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
// startup log message.
app.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});
