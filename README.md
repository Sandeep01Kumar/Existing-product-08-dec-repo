# hao-backprop-test

This is a test project for backprop integration.

It is a minimal Python 3 **Flask** application that answers every request, on
every path, with HTTP `200`, a `Content-Type: text/plain` header, and the body
`Hello, World!` followed by a trailing newline. The app binds to
`127.0.0.1:3000` (loopback only) and prints `Server running at http://127.0.0.1:3000/`
on startup. It has no configuration or environment variables and no separate
endpoints — every request receives the same response.

## Requirements

- Python `>=3.9`
- Flask `3.1.3` (pinned in `requirements.txt`)

## Setup and run

```bash
# Create a virtual environment
python -m venv venv

# Activate it (macOS/Linux)
source venv/bin/activate
# On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Once started, the app is reachable at http://127.0.0.1:3000/.
