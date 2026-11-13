"""LINE echo bot. Python 3.10+, standard library only; local demo server."""
import base64
import hashlib
import hmac
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPLY_URL = "https://api.line.me/v2/bot/message/reply"
LOG = logging.getLogger(__name__)


def verify_signature(body, signature, secret):
    """Verify original bytes BEFORE parsing JSON; never reserialize first."""
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    expected = base64.b64encode(digest)
    return hmac.compare_digest(expected, signature.encode("utf-8"))


def reply_text(token, reply_token, text):
    """Reply tokens are single-use. Do not blindly retry this POST."""
    payload = {"replyToken": reply_token,
               "messages": [{"type": "text", "text": text}]}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(REPLY_URL, data=data, method="POST", headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"})
    with urlopen(req, timeout=10) as response:
        response.read()


def process_webhook(body, signature, secret, token, sender=reply_text):
    """Return an HTTP status; sender is injectable for offline tests."""
    if not verify_signature(body, signature, secret):
        return 400
    try:
        payload = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return 400
    if not isinstance(payload, dict):
        return 400
    events = payload.get("events")
    if not isinstance(events, list):
        return 400
    # Verification sends an empty events array: acknowledge without replying.
    for event in events:
        if not isinstance(event, dict):
            return 400
        message = event.get("message", {})
        if (event.get("type") != "message"
                or not isinstance(message, dict)
                or message.get("type") != "text"):
            continue
        if event.get("mode") == "standby":
            continue
        reply_token = event.get("replyToken")
        text = message.get("text")
        if not isinstance(reply_token, str) or not reply_token:
            continue
        if not isinstance(text, str) or not text:
            continue
        try:
            sender(token, reply_token, text)
        except (HTTPError, URLError, TimeoutError, OSError):
            # Do not log user messages, credentials, or reply tokens.
            LOG.error("LINE reply request failed")
            return 502
    return 200


def make_handler(secret, token):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/callback":
                self.send_error(404)
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_error(400)
                return
            if not 0 < size <= 1024 * 1024:
                self.send_error(413)
                return
            self.connection.settimeout(15)
            try:
                body = self.rfile.read(size)
            except (TimeoutError, OSError):
                self.send_error(408)
                return
            if len(body) != size:
                self.send_error(400)
                return
            signature = self.headers.get("X-Line-Signature", "")
            status = process_webhook(body, signature, secret, token)
            response = b"OK" if status == 200 else b"Rejected"
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)
    return Handler


def main():
    secret = os.environ.get("LINE_CHANNEL_SECRET", "").strip()
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    if not secret or not token:
        raise SystemExit("Set LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN")
    # HTTP is local only; ngrok terminates public HTTPS during development.
    server = HTTPServer(("127.0.0.1", 8000), make_handler(secret, token))
    print("Listening on http://127.0.0.1:8000/callback")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
