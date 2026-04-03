from __future__ import annotations

import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from urllib import error, request
from urllib.parse import urlsplit

from .config import Settings


class LocalRuntimeError(RuntimeError):
    """Raised when the repo-supported Ollama workflow cannot be prepared or started."""


@dataclass(frozen=True, slots=True)
class LocalRuntimeStatus:
    runtime: str
    command: str
    base_url: str
    model: str
    runtime_available: bool
    server_running: bool
    model_available: bool


def _ollama_origin(base_url: str) -> str:
    parsed = urlsplit(base_url)
    if not parsed.scheme or not parsed.netloc:
        raise LocalRuntimeError(
            "ELIZA_RAG_LLM_BASE_URL must be a valid URL when using the local Ollama backend."
        )
    return f"{parsed.scheme}://{parsed.netloc}"


class OllamaRuntimeManager:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._command = settings.local_llm_runtime_command
        self._model = self._resolve_model(settings)
        self._base_url = self._resolve_base_url(settings).rstrip("/")
        self._origin = _ollama_origin(self._base_url)
        self._timeout_seconds = settings.local_llm_start_timeout_seconds

    def _resolve_base_url(self, settings: Settings) -> str:
        if settings.llm_provider.strip().lower() == "local_ollama":
            return settings.llm_base_url
        return settings.local_llm_base_url

    def _resolve_model(self, settings: Settings) -> str:
        if settings.llm_provider.strip().lower() == "local_ollama":
            return settings.llm_model
        return settings.local_llm_model

    @property
    def command(self) -> str:
        return self._command

    @property
    def model(self) -> str:
        return self._model

    @property
    def base_url(self) -> str:
        return self._base_url

    def status(self) -> LocalRuntimeStatus:
        runtime_available = shutil.which(self._command) is not None
        server_running = False
        model_available = False
        if runtime_available:
            server_running = self._is_server_running()
            if server_running:
                model_available = self._model in self._list_models()
        return LocalRuntimeStatus(
            runtime="ollama",
            command=self._command,
            base_url=self._base_url,
            model=self._model,
            runtime_available=runtime_available,
            server_running=server_running,
            model_available=model_available,
        )

    def ensure_ready(self) -> LocalRuntimeStatus:
        status = self.status()
        if not status.runtime_available:
            raise LocalRuntimeError(
                f"Local runtime `{self._command}` is not installed or not on PATH. "
                "Install Ollama, then run `uv run eliza-rag-local-llm prepare`."
            )
        if not status.server_running:
            self._start_server()
            status = self.status()
        if not status.server_running:
            raise LocalRuntimeError(
                f"Local Ollama runtime did not become ready at {self._base_url}."
            )
        if not status.model_available:
            raise LocalRuntimeError(
                f"Local Ollama model `{self._model}` is not available. "
                "Run `uv run eliza-rag-local-llm prepare` to pull it."
            )
        return status

    def prepare(self, *, pull: bool = True) -> LocalRuntimeStatus:
        status = self.status()
        if not status.runtime_available:
            raise LocalRuntimeError(
                f"Local runtime `{self._command}` is not installed or not on PATH. "
                "Install Ollama before preparing the local Ollama workflow."
            )
        if not status.server_running:
            self._start_server()
        if pull and self._model not in self._list_models():
            self._pull_model()
        return self.status()

    def start(self) -> LocalRuntimeStatus:
        status = self.status()
        if not status.runtime_available:
            raise LocalRuntimeError(
                f"Local runtime `{self._command}` is not installed or not on PATH. "
                "Install Ollama before starting the local Ollama workflow."
            )
        if not status.server_running:
            self._start_server()
        return self.status()

    def _is_server_running(self) -> bool:
        try:
            self._request_json(f"{self._origin}/api/tags", timeout=2)
        except LocalRuntimeError:
            return False
        return True

    def _list_models(self) -> set[str]:
        payload = self._request_json(f"{self._origin}/api/tags", timeout=5)
        models = payload.get("models")
        if not isinstance(models, list):
            raise LocalRuntimeError("Local Ollama runtime returned an unexpected model listing payload.")
        result: set[str] = set()
        for item in models:
            if isinstance(item, dict):
                name = item.get("name")
                if isinstance(name, str) and name.strip():
                    result.add(name.strip())
        return result

    def _start_server(self) -> None:
        try:
            process = subprocess.Popen(
                [self._command, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as exc:
            raise LocalRuntimeError(
                f"Failed to start local Ollama runtime with `{self._command} serve`: {exc}"
            ) from exc

        deadline = time.monotonic() + self._timeout_seconds
        while time.monotonic() < deadline:
            if self._is_server_running():
                return
            if process.poll() is not None:
                raise LocalRuntimeError(
                    f"Local Ollama runtime exited before becoming ready at {self._base_url}."
                )
            time.sleep(0.5)

        raise LocalRuntimeError(
            f"Timed out waiting for local Ollama runtime at {self._base_url}."
        )

    def _pull_model(self) -> None:
        try:
            completed = subprocess.run(
                [self._command, "pull", self._model],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError as exc:
            raise LocalRuntimeError(
                f"Failed to pull local Ollama model `{self._model}`: {exc}"
            ) from exc

        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
            raise LocalRuntimeError(
                f"Failed to pull local Ollama model `{self._model}`: {detail}"
            )

    def _request_json(self, url: str, *, timeout: int) -> dict[str, object]:
        http_request = request.Request(url, method="GET")
        try:
            with request.urlopen(http_request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except error.URLError as exc:
            raise LocalRuntimeError(str(exc.reason)) from exc
        except json.JSONDecodeError as exc:
            raise LocalRuntimeError("Local Ollama runtime returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise LocalRuntimeError("Local Ollama runtime returned a non-object JSON payload.")
        return payload


def build_local_runtime_manager(settings: Settings) -> OllamaRuntimeManager:
    runtime = settings.local_llm_runtime.strip().lower()
    if runtime != "ollama":
        raise LocalRuntimeError(
            f"Unsupported local runtime `{settings.local_llm_runtime}`. Expected `ollama`."
        )
    return OllamaRuntimeManager(settings)
