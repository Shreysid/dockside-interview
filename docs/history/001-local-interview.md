# 001 Local interview

## Summary

Dockside Interview starts with a Python standard-library HTTP service and a health endpoint.

## Motivation

The browser workspace and local model adapters need a shared HTTP entry point with a consistent local access policy.

## Design

The service binds to IPv4 loopback. Every request must supply the exact numeric loopback Host and service port. If an Origin is present it must match the service URL. Methods other than GET and HEAD require an explicit matching Origin.

## Implementation

Run `python3 -m dockside.server` and visit `http://127.0.0.1:8765/health`. Use `--port` to change the port. Run `python3 -m unittest discover -v` to exercise the policy with real HTTP connections on a temporary loopback port.

## Files Changed

- `dockside/server.py` provides the HTTP entry point and request policy.
- `tests/test_server.py` exercises routing and policy enforcement.
- `LICENSE` and `.gitignore` establish licensing and exclude local artifacts from version control.

## Tradeoffs

The service handles one connection at a time and applies a five-second socket inactivity timeout. This timeout does not impose a total request deadline. The URL must use the numeric loopback address.

## Future Work

Add the interview workspace and session workflow, bound API request bodies and engine calls, and connect the local speech and language model adapters.
