import http.client
from http.server import HTTPServer
import json
import threading
import unittest

from dockside.server import DocksideHandler, LOOPBACK


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

    def request(self, method="GET", path="/health", *, hosts=None, origins=()):
        connection = http.client.HTTPConnection(self.host, timeout=2)
        try:
            connection.putrequest(method, path, skip_host=True)
            for host in [self.host] if hosts is None else hosts:
                connection.putheader("Host", host)
            for origin in origins:
                connection.putheader("Origin", origin)
            connection.endheaders()
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

    def test_rejects_foreign_null_and_duplicate_origin(self):
        origin = f"http://{self.host}"
        for origins in (["https://example.com"], ["null"], [origin, origin]):
            with self.subTest(origins=origins):
                self.assertEqual(self.request(origins=origins)[0], 403)

    def test_post_requires_same_origin_before_routing(self):
        self.assertEqual(self.request(method="POST")[0], 403)
        self.assertEqual(self.request(method="POST", origins=[f"http://{self.host}"])[0], 501)
