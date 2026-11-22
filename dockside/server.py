"""Loopback HTTP entry point for Dockside Interview."""

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
import re

from dockside.interviewer import MAX_TURN_BYTES, InterviewerUnavailable, interview, validate_turn
from dockside.problems import PROBLEMS
from dockside.speech import MAX_SPEECH_BYTES, SpeechUnavailable, synthesize
from dockside.transcription import (
    DEMUXERS,
    MAX_AUDIO_BYTES,
    InvalidRecording,
    TranscriberUnavailable,
    transcribe,
)

LOOPBACK = "127.0.0.1"
REQUEST_IDLE_TIMEOUT = 5


class DocksideHandler(BaseHTTPRequestHandler):
    timeout = REQUEST_IDLE_TIMEOUT

    def parse_request(self):
        if not super().parse_request():
            return False

        host = f"{LOOPBACK}:{self.server.server_port}"
        if self.headers.get_all("Host") != [host]:
            self.send_error(HTTPStatus.FORBIDDEN, "Invalid Host")
            return False

        origins = self.headers.get_all("Origin")
        requires_origin = self.command not in ("GET", "HEAD")
        if origins != [f"http://{host}"] and (origins is not None or requires_origin):
            self.send_error(HTTPStatus.FORBIDDEN, "Invalid Origin")
            return False
        return True

    def do_GET(self):
        self.send_read_response()

    def do_HEAD(self):
        self.send_read_response()

    def do_POST(self):
        if self.path == "/api/interview":
            body = self.read_upload(MAX_TURN_BYTES, ("application/json",))
            if body is not None:
                self.submit_turn(body)
        elif self.path == "/api/transcribe":
            body = self.read_upload(MAX_AUDIO_BYTES, DEMUXERS)
            if body is not None:
                self.submit_recording(body)
        elif self.path == "/api/speech":
            body = self.read_upload(MAX_SPEECH_BYTES, ("text/plain",))
            if body is not None:
                self.submit_speech(body)
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def read_upload(self, max_bytes, media_types):
        lengths = self.headers.get_all("Content-Length", [])
        if (
            self.headers.get_all("Transfer-Encoding") is not None
            or len(lengths) != 1
            or not re.fullmatch(r"[0-9]{1,10}", lengths[0])
        ):
            self.send_json({"error": "Expected one valid Content-Length"}, HTTPStatus.BAD_REQUEST)
            return
        size = int(lengths[0])
        if size > max_bytes:
            self.send_json({"error": "Upload is too large"}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return
        content_types = self.headers.get_all("Content-Type", [])
        if len(content_types) != 1 or self.headers.get_content_type() not in media_types:
            self.send_json({"error": "Unsupported media type"}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
            return

        try:
            body = self.rfile.read(size)
        except TimeoutError:
            self.send_json({"error": "Upload timed out"}, HTTPStatus.REQUEST_TIMEOUT)
            return
        if len(body) != size:
            self.send_json({"error": "Incomplete upload"}, HTTPStatus.BAD_REQUEST)
            return
        return body

    def submit_turn(self, body):
        try:
            turn = validate_turn(json.loads(body.decode("utf-8")))
        except (ValueError, RecursionError):
            self.send_json({"error": "Invalid interview turn"}, HTTPStatus.BAD_REQUEST)
            return

        try:
            reply = interview(*turn)
        except InterviewerUnavailable:
            self.send_json({"error": "Local interviewer unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
            return
        self.send_json({"reply": reply})

    def submit_recording(self, body):
        try:
            transcript = transcribe(body, self.headers.get_content_type())
        except InvalidRecording:
            self.send_json({"error": "Invalid recording"}, HTTPStatus.BAD_REQUEST)
            return
        except TranscriberUnavailable:
            self.send_json({"error": "Local transcriber unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
            return
        self.send_json({"transcript": transcript})

    def send_read_response(self):
        if self.path == "/health":
            payload = {"status": "ok"}
        elif self.path == "/api/problems":
            payload = {"problems": PROBLEMS}
        else:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        self.send_json(payload)

    def submit_speech(self, body):
        try:
            text = body.decode("utf-8")
            if not text.strip() or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", text):
                raise ValueError
        except ValueError:
            self.send_json({"error": "Expected nonempty UTF-8 speech text"}, HTTPStatus.BAD_REQUEST)
            return

        try:
            wav = synthesize(text.strip())
        except SpeechUnavailable:
            self.send_json({"error": "Local speech engine unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
            return
        self.send_body(wav, "audio/wav")

    def send_json(self, payload, status=HTTPStatus.OK):
        body = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
        self.send_body(body, "application/json", status)

    def send_body(self, body, media_type, status=HTTPStatus.OK):
        self.send_response(status)
        self.send_header("Content-Type", media_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def log_message(self, format, *args):
        # Request targets can contain private data.
        pass


def main():
    parser = argparse.ArgumentParser(description="Run Dockside Interview locally.")
    parser.add_argument("--port", type=int, default=8765, metavar="1024-65535")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("--port must be between 1024 and 65535")
    with HTTPServer((LOOPBACK, args.port), DocksideHandler) as server:
        print(
            f"Dockside Interview is listening on http://{LOOPBACK}:{server.server_port}",
            flush=True,
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
