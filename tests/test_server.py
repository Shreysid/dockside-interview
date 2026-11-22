import http.client
from http.server import HTTPServer
import json
import threading
import unittest
from unittest.mock import patch

from dockside.interviewer import InterviewerUnavailable, MAX_TURN_BYTES
from dockside.server import DocksideHandler, LOOPBACK
from dockside.speech import MAX_SPEECH_BYTES, SpeechUnavailable
from dockside.transcription import MAX_AUDIO_BYTES, InvalidRecording, TranscriberUnavailable


class LoopbackTests(unittest.TestCase):
    def setUp(self):
        self.server = HTTPServer((LOOPBACK, 0), DocksideHandler)
        self.addCleanup(self.server.server_close)
        self.thread = threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.01}
        )
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.host = f"{LOOPBACK}:{self.server.server_port}"

    def stop_server(self):
        self.server.shutdown()
        self.thread.join()

    def request(self, method="GET", path="/health", *, hosts=None, origins=(), headers=(), body=None):
        connection = http.client.HTTPConnection(self.host, timeout=2)
        try:
            connection.putrequest(method, path, skip_host=True)
            for host in [self.host] if hosts is None else hosts:
                connection.putheader("Host", host)
            for origin in origins:
                connection.putheader("Origin", origin)
            for name, value in headers:
                connection.putheader(name, value)
            connection.endheaders(body)
            response = connection.getresponse()
            return response.status, response.read()
        finally:
            connection.close()

    def test_health_accepts_navigation_and_same_origin(self):
        self.assertEqual(self.server.server_address[0], LOOPBACK)
        self.assertEqual(self.request(), (200, b'{"status":"ok"}\n'))
        self.assertEqual(self.request(origins=[f"http://{self.host}"])[0], 200)
        self.assertEqual(self.request(method="HEAD"), (200, b""))
        self.assertEqual(self.request(path="/missing")[0], 404)

    def test_rejects_missing_foreign_and_duplicate_host(self):
        for hosts in ([], ["example.com"], [self.host, self.host]):
            with self.subTest(hosts=hosts):
                self.assertEqual(self.request(hosts=hosts)[0], 403)

    def test_problem_catalog_is_readable_and_protected(self):
        path = "/api/problems"
        status, body = self.request(path=path, origins=[f"http://{self.host}"])
        self.assertEqual(status, 200)
        problems = json.loads(body)["problems"]
        self.assertGreaterEqual(len(problems), 3)
        ids = [problem["id"] for problem in problems]
        self.assertEqual(len(set(ids)), len(ids))
        for problem in problems:
            for field in ("id", "title", "prompt", "constraints", "example", "starter_code"):
                self.assertIsInstance(problem[field], str)
                self.assertTrue(problem[field].strip())
        self.assertEqual(self.request(method="HEAD", path=path), (200, b""))
        self.assertEqual(self.request(path=path, hosts=["example.com"])[0], 403)
        self.assertEqual(self.request(path=path, origins=["https://example.com"])[0], 403)

    def test_workspace_assets_are_readable_and_protected(self):
        for path, marker in (
            ("/", b'id="code"'),
            ("/workspace.css", b".workspace"),
            ("/turn-detection.mjs", b"createTurnDetector"),
            ("/workspace.js", b'"/api/interview"'),
        ):
            with self.subTest(path=path):
                status, body = self.request(path=path)
                self.assertEqual(status, 200)
                self.assertIn(marker, body)
                self.assertEqual(self.request(method="HEAD", path=path), (200, b""))
                self.assertEqual(self.request(path=path, hosts=["example.com"])[0], 403)
                self.assertEqual(self.request(path=path, origins=["https://example.com"])[0], 403)
        self.assertEqual(self.request(path="/dockside/server.py")[0], 404)

    def test_rejects_foreign_null_and_duplicate_origin(self):
        origin = f"http://{self.host}"
        for origins in (["https://example.com"], ["null"], [origin, origin]):
            with self.subTest(origins=origins):
                self.assertEqual(self.request(origins=origins)[0], 403)

    def test_post_requires_same_origin_before_routing(self):
        self.assertEqual(self.request(method="POST")[0], 403)
        self.assertEqual(self.request(method="POST", origins=[f"http://{self.host}"])[0], 404)

    def submit_turn(self, body, *, content_type="application/json", length=None):
        return self.request(
            "POST", "/api/interview",
            origins=[f"http://{self.host}"],
            headers=[
                ("Content-Type", content_type),
                ("Content-Length", str(len(body) if length is None else length)),
            ],
            body=body,
        )

    @patch("dockside.server.interview")
    def test_valid_turn_calls_interviewer_and_engine_failure_is_reported(self, interview):
        body = b'{"problem_id":"locker-utilization","intent":"check","code":"pass","text":""}'
        interview.return_value = "What happens when intervals touch?"
        status, response = self.submit_turn(body)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(response), {"reply": interview.return_value})
        interview.assert_called_once_with("locker-utilization", "check", "pass", "", [])
        interview.side_effect = InterviewerUnavailable("private error")
        status, response = self.submit_turn(body)
        self.assertEqual(status, 503)
        self.assertEqual(json.loads(response), {"error": "Local interviewer unavailable"})

    @patch("dockside.server.interview")
    def test_turn_accepts_bounded_history(self, interview):
        interview.return_value = "How would you handle ties?"
        message = {"role": "candidate", "text": "é" * 200}
        turn = {"problem_id": "locker-utilization", "intent": "reply", "code": "pass", "text": "Yes"}
        history = [message] * 6
        self.assertEqual(self.submit_turn(json.dumps({**turn, "history": history}).encode())[0], 200)
        interview.assert_called_once_with("locker-utilization", "reply", "pass", "Yes", history)
        interview.reset_mock()

        for invalid_history in (
            None,
            [message] * 7,
            [{**message, "text": message["text"] + "a"}],
            [{**message, "role": "system"}],
            [{**message, "extra": 1}],
        ):
            with self.subTest(history=invalid_history):
                body = json.dumps({**turn, "history": invalid_history}).encode()
                self.assertEqual(self.submit_turn(body)[0], 400)
        interview.assert_not_called()

    @patch("dockside.server.interview")
    def test_invalid_requests_never_reach_model(self, interview):
        self.assertEqual(self.request("POST", "/api/interview")[0], 403)
        self.assertEqual(self.submit_turn(b"", length=MAX_TURN_BYTES + 1)[0], 413)
        self.assertEqual(self.submit_turn(b"{}", content_type="text/plain")[0], 415)
        for body in (
            b"{",
            b'{"problem_id":"unknown","intent":"check","code":"","text":""}',
            b'{"problem_id":"locker-utilization","intent":"reply","code":"","text":" "}',
            b'{"problem_id":"locker-utilization","intent":"check","code":"\\ud800","text":""}',
        ):
            with self.subTest(body=body):
                self.assertEqual(self.submit_turn(body)[0], 400)
        interview.assert_not_called()

    @patch("dockside.server.transcribe")
    def test_audio_upload_returns_transcript_or_reports_local_failure(self, transcribe):
        def upload():
            return self.request(
                "POST", "/api/transcribe",
                origins=[f"http://{self.host}"],
                headers=[("Content-Type", "audio/webm;codecs=opus"), ("Content-Length", "5")],
                body=b"audio",
            )

        for transcript in ("Try a heap.", ""):
            with self.subTest(transcript=transcript):
                transcribe.return_value = transcript
                status, body = upload()
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(body), {"transcript": transcript})
                transcribe.assert_called_with(b"audio", "audio/webm")

        for error, status in ((InvalidRecording, 400), (TranscriberUnavailable, 503)):
            with self.subTest(error=error):
                transcribe.side_effect = error("private engine detail")
                actual_status, body = upload()
                self.assertEqual(actual_status, status)
                self.assertNotIn(b"private engine detail", body)

    @patch("dockside.server.transcribe")
    def test_audio_upload_validates_access_and_framing_before_transcribing(self, transcribe):
        origin = f"http://{self.host}"
        for hosts, origins, headers, status in (
            (["example.com"], [origin], [("Content-Length", "0")], 403),
            (None, [], [("Content-Length", "0")], 403),
            (None, [origin], [], 400),
            (None, [origin], [("Content-Length", "0")] * 2, 400),
            (None, [origin], [("Content-Length", "0"), ("Transfer-Encoding", "chunked")], 400),
            (None, [origin], [("Content-Length", str(MAX_AUDIO_BYTES + 1))], 413),
            (None, [origin], [("Content-Length", "0"), ("Content-Type", "text/plain")], 415),
            (None, [origin], [("Content-Length", "0")] + [("Content-Type", "audio/ogg")] * 2, 415),
        ):
            with self.subTest(hosts=hosts, origins=origins, headers=headers):
                response, _ = self.request(
                    "POST", "/api/transcribe", hosts=hosts, origins=origins, headers=headers,
                )
                self.assertEqual(response, status)
        transcribe.assert_not_called()

    @patch("dockside.server.synthesize")
    def test_speech_renders_valid_text_and_reports_engine_failure(self, synthesize):
        origin = f"http://{self.host}"

        def upload(body, *, origins=(origin,), length=None, media_type="text/plain", voices=()):
            return self.request(
                "POST", "/api/speech", origins=origins,
                headers=[
                    ("Content-Type", media_type),
                    ("Content-Length", str(len(body) if length is None else length)),
                    *(("X-Dockside-Voice", voice) for voice in voices),
                ],
                body=body,
            )

        self.assertEqual(upload(b"hello", origins=())[0], 403)
        self.assertEqual(upload(b"", length=MAX_SPEECH_BYTES + 1)[0], 413)
        self.assertEqual(upload(b"hello", media_type="application/json")[0], 415)
        for body in (b" \n", b"\xff", b"hello\x00"):
            self.assertEqual(upload(body)[0], 400)
        for voices in (("",), ("unknown",), ("af_bella", "af_bella"), ("af_heart, af_bella",)):
            self.assertEqual(upload(b"hello", voices=voices)[0], 400)
        synthesize.assert_not_called()

        synthesize.return_value = b"RIFF....WAVE"
        self.assertEqual(upload(b" What happens next? "), (200, synthesize.return_value))
        synthesize.assert_called_once_with("What happens next?", "af_heart")
        for voice in ("af_heart", "af_bella", "am_michael"):
            self.assertEqual(upload(b"hello", voices=(voice,)), (200, synthesize.return_value))
            synthesize.assert_called_with("hello", voice)

        synthesize.side_effect = SpeechUnavailable("private engine detail")
        status, body = upload(b"Try a heap.")
        self.assertEqual(status, 503)
        self.assertEqual(json.loads(body), {"error": "Local speech engine unavailable"})
