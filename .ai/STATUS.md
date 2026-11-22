# Project status

The MIT-licensed service exposes `/health` and a three-problem catalog at `/api/problems` under loopback Host and Origin checks. The project uses a locked, dependency-free uv environment. HTTP integration tests cover both routes and access policy.

The service also accepts typed turns, code checks, and finish requests through a bounded endpoint backed by local Ollama. The candidate workspace, conversation history, voice engines, and full setup guide are pending.
