"""ASGI request ID middleware and request-scoped context tracking."""

import logging
import re
import uuid
from contextvars import ContextVar
from typing import Any, Callable, MutableMapping, Optional

REQUEST_ID_HEADER = b"x-request-id"
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9\-]{8,64}$")

_current_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def current_request_id() -> Optional[str]:
    """Return the current request ID from contextvar or None if not in request context."""
    return _current_request_id.get()


class RequestIdMiddleware:
    """Pure ASGI middleware to assign/propagate x-request-id."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(
        self,
        scope: MutableMapping[str, Any],
        receive: Callable[..., Any],
        send: Callable[..., Any],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming_rid: Optional[str] = None
        for key, value in scope.get("headers", []):
            if key.lower() == REQUEST_ID_HEADER:
                try:
                    incoming_rid = value.decode("latin-1")
                except Exception:
                    incoming_rid = None
                break

        if incoming_rid and _REQUEST_ID_RE.match(incoming_rid):
            rid = incoming_rid
        else:
            rid = uuid.uuid4().hex

        token = _current_request_id.set(rid)

        async def send_wrapper(message: MutableMapping[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", rid.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            _current_request_id.reset(token)


_log_factory_installed = False


def install_log_record_factory() -> None:
    """Wrap logging.getLogRecordFactory() to inject request_id attribute. Idempotent."""
    global _log_factory_installed
    if _log_factory_installed:
        return
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = old_factory(*args, **kwargs)
        record.request_id = current_request_id() or "-"
        return record

    logging.setLogRecordFactory(record_factory)
    _log_factory_installed = True

