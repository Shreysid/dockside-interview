"""Loopback HTTP entry point for Dockside Interview."""

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer

from dockside.problems import PROBLEMS

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

    def send_read_response(self):
        if self.path == "/health":
            payload = {"status": "ok"}
        elif self.path == "/api/problems":
            payload = {"problems": PROBLEMS}
        else:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        body = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command == "GET":
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
