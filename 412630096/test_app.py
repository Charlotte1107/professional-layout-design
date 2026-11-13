"""Offline behavior tests: no LINE account or network required."""
import base64
import hashlib
import hmac
import json
import unittest
from unittest.mock import Mock, patch
from urllib.error import URLError
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


if __name__ == "__main__":
    unittest.main()
