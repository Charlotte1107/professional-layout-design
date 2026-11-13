"""Offline behavior tests: no LINE account or network required."""
import base64
import hashlib
import hmac
import json
import unittest
import threading
from http.client import HTTPConnection
from http.server import HTTPServer
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
import app

SECRET = "test-secret"
TOKEN = "test-token"


def signed(payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    signature = base64.b64encode(hmac.new(
        SECRET.encode(), body, hashlib.sha256).digest()).decode()
    return body, signature


def event(text="你好 LINE"):
    return {"type": "message", "mode": "active", "replyToken": "test-reply",
            "message": {"type": "text", "text": text}}


class WebhookTests(unittest.TestCase):
    def run_payload(self, payload, sender):
        body, signature = signed(payload)
        return app.process_webhook(body, signature, SECRET, TOKEN, sender)

    def test_signed_text_is_replied(self):
        sender = Mock()
        self.assertEqual(self.run_payload({"events": [event()]}, sender), 200)
        sender.assert_called_once_with(TOKEN, "test-reply", "你好 LINE")

    def test_tampered_body_never_replies(self):
        body, signature = signed({"events": [event()]})
        sender = Mock()
        status = app.process_webhook(body + b" ", signature, SECRET, TOKEN, sender)
        self.assertEqual(status, 400)
        sender.assert_not_called()

    def test_missing_signature_rejected(self):
        self.assertEqual(app.process_webhook(b"{}", "", SECRET, TOKEN), 400)

    def test_empty_events_verify(self):
        sender = Mock()
        self.assertEqual(self.run_payload({"events": []}, sender), 200)
        sender.assert_not_called()

    def test_non_text_and_standby_ignored(self):
        sender = Mock()
        standby = event()
        standby["mode"] = "standby"
        image = {"type": "message", "message": {"type": "image"}}
        self.assertEqual(self.run_payload({"events": [image, standby]}, sender), 200)
        sender.assert_not_called()

    def test_invalid_structure(self):
        for payload in [[], {}, {"events": "wrong"}, {"events": [None]}]:
            self.assertEqual(self.run_payload(payload, Mock()), 400)

    def test_signed_invalid_json(self):
        body = b"{invalid"
        sig = base64.b64encode(hmac.new(SECRET.encode(), body, hashlib.sha256).digest()).decode()
        self.assertEqual(app.process_webhook(body, sig, SECRET, TOKEN), 400)

    def test_network_error_is_502(self):
        sender = Mock(side_effect=URLError("offline"))
        with self.assertLogs(app.LOG, level="ERROR"):
            self.assertEqual(self.run_payload({"events": [event()]}, sender), 502)

    @patch("app.urlopen")
    def test_outgoing_reply_request(self, opener):
        app.reply_text(TOKEN, "test-reply", "你好")
        req = opener.call_args.args[0]
        self.assertEqual(req.full_url, app.REPLY_URL)
        self.assertEqual(req.get_header("Authorization"), "Bearer " + TOKEN)
        self.assertEqual(json.loads(req.data)["messages"][0]["text"], "你好")
        self.assertEqual(opener.call_args.kwargs["timeout"], 10)


class HTTPReceiverTests(unittest.TestCase):
    def send(self, path="/callback", body=b"{}", headers=None):
        handler = app.make_handler(SECRET, TOKEN)
        handler.log_message = lambda *args: None
        with HTTPServer(("127.0.0.1", 0), handler) as server:
            server.timeout = 3
            worker = threading.Thread(target=server.handle_request, daemon=True)
            worker.start()
            connection = HTTPConnection(*server.server_address, timeout=3)
            try:
                connection.request("POST", path, body=body, headers=headers or {})
                response = connection.getresponse()
                status, data = response.status, response.read()
            finally:
                connection.close()
                worker.join(timeout=4)
            self.assertFalse(worker.is_alive())
            return status, data

    def test_http_valid_verify(self):
        body, sig = signed({"events": []})
        self.assertEqual(self.send(body=body, headers={"X-Line-Signature": sig}),
                         (200, b"OK"))

    def test_http_wrong_path(self):
        self.assertEqual(self.send(path="/wrong")[0], 404)

    def test_http_invalid_signature(self):
        self.assertEqual(self.send()[0], 400)

    def test_http_oversized(self):
        self.assertEqual(self.send(headers={"Content-Length": "1048577"})[0], 413)

    def test_http_invalid_length(self):
        self.assertEqual(self.send(headers={"Content-Length": "bad"})[0], 400)

    def test_http_empty_body(self):
        self.assertEqual(self.send(body=b"")[0], 413)

    def test_http_reply_failure(self):
        body, sig = signed({"events": [event()]})
        with patch("app.urlopen", side_effect=URLError("offline")):
            with self.assertLogs(app.LOG, level="ERROR"):
                self.assertEqual(self.send(body=body, headers={
                    "X-Line-Signature": sig}), (502, b"Rejected"))

    def test_api_error_log_contains_only_status(self):
        body, sig = signed({"events": [event()]})
        sender = Mock(side_effect=HTTPError(app.REPLY_URL, 401, TOKEN, {}, None))
        with self.assertLogs(app.LOG, level="ERROR") as captured:
            self.assertEqual(app.process_webhook(
                body, sig, SECRET, TOKEN, sender), 502)
        self.assertIn("401", " ".join(captured.output))
        self.assertNotIn(TOKEN, " ".join(captured.output))


if __name__ == "__main__":
    unittest.main()
