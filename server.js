/**
 * @module server
 * @description Minimal HTTP server for Backprop integration testing.
 * Creates a basic HTTP server that responds to all requests with "Hello, World!".
 * @version 1.0.0
 * @author hxu
 * @license MIT
 */

// Import Node.js built-in HTTP module for creating the server
const http = require('http');

/**
 * Server binding address.
 * Set to localhost (127.0.0.1) for local development - restricts access to local machine only.
 * @const {string}
 * @default '127.0.0.1'
 */
const hostname = '127.0.0.1';

/**
 * Server listening port number.
 * Port 3000 is commonly used for Node.js development servers.
 * @const {number}
 * @default 3000
 */
const port = 3000;

/**
 * HTTP server instance created with request handler callback.
 * The server responds to all incoming HTTP requests with a "Hello, World!" message.
 * @type {http.Server}
 */
const server = http.createServer(
  /**
   * Request handler callback - processes all incoming HTTP requests.
   * @param {http.IncomingMessage} req - The incoming request object
   * @param {http.ServerResponse} res - The server response object
   */
  (req, res) => {
    // Set HTTP status code to 200 (OK) indicating successful request
    res.statusCode = 200;
    // Set Content-Type header to indicate plain text response
    res.setHeader('Content-Type', 'text/plain');
    // Send the response body and end the response
    res.end('Hello, World!\n');
  }
);

// Start the server and begin listening for connections on the specified hostname and port
server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});
