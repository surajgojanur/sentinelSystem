import json

from app.services import ai_service


class _FakeResponse:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_get_ai_response_dispatches_to_ollama(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "mistral")

    captured = {}

    def _fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse({"message": {"content": "Ollama says hi"}})

    monkeypatch.setattr(ai_service.urllib.request, "urlopen", _fake_urlopen)

    response = ai_service.get_ai_response([{"role": "user", "content": "Hello"}])

    assert response == "Ollama says hi"
    assert captured["url"] == "http://127.0.0.1:11434/api/chat"
    assert captured["timeout"] == 60.0
    assert captured["body"]["model"] == "mistral"
    assert captured["body"]["stream"] is False
    assert captured["body"]["messages"][0]["role"] == "system"
    assert captured["body"]["messages"][1] == {"role": "user", "content": "Hello"}


def test_ollama_response_reports_connection_errors(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "ollama")

    def _fake_urlopen(request, timeout):
        raise ai_service.urllib.error.URLError("connection refused")

    monkeypatch.setattr(ai_service.urllib.request, "urlopen", _fake_urlopen)

    response = ai_service.get_ai_response([{"role": "user", "content": "Hello"}])

    assert "could not reach the Ollama server" in response
    assert "OLLAMA_BASE_URL" in response
