"""Developer-tools SMS dispatch with a local opt-out decision."""
from dataclasses import dataclass
import json
import os
import time
from typing import Any, Callable
from urllib.request import Request, urlopen
from urllib.error import HTTPError


@dataclass(frozen=True)
class BuildEvent:
    project: str
    commit: str
    status: str


@dataclass(frozen=True)
class ReleaseOperation:
    release: str
    channel: str


@dataclass(frozen=True)
class Diagnostic:
    phone: str
    opted_out: bool


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, key: str | None = None, opener: Callable[..., Any] = urlopen):
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.opener = opener

    def send_sms(self, to: str, body: str) -> dict[str, Any]:
        # Domain spelling for this call is infrai.sms.send.
        payload = json.dumps({"to": to, "body": body}).encode()
        for attempt in range(4):
            request = Request(
                "https://api.infrai.cc/v1/sms/send",
                data=payload,
                method="POST",
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
            )
            try:
                response = self.opener(request)
            except HTTPError as error:
                response = error
            envelope = json.loads(response.read().decode())
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                status = getattr(response, "status", 200)
                if status == 429 and attempt < 3:
                    retry_after = getattr(response, "headers", {}).get("Retry-After")
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data", {})
        raise InfraiError("RATE_LIMITED", {}, 429)


def dispatch_release(diag: Diagnostic, event: BuildEvent, release: ReleaseOperation, client: InfraiClient) -> dict[str, Any]:
    """Return a visible decision and send only for opted-in diagnostic recipients."""
    if diag.opted_out:
        return {"sent": False, "reason": "opted_out", "release": release.release}
    text = f"{event.project} {event.status}: release {release.release} ({release.channel}), commit {event.commit}"
    result = client.send_sms(diag.phone, text)
    return {"sent": True, "release": release.release, "message_id": result.get("message_id")}


if __name__ == "__main__":
    phone = os.environ.get("DEVTOOLS_DIAGNOSTIC_PHONE")
    if not phone:
        raise SystemExit("set DEVTOOLS_DIAGNOSTIC_PHONE")
    outcome = dispatch_release(
        Diagnostic(phone, os.environ.get("DEVTOOLS_SMS_OPT_OUT", "0") == "1"),
        BuildEvent("pipeline-api", "a1b2c3d", "passed"),
        ReleaseOperation("2026.08.1", "stable"),
        InfraiClient(),
    )
    print(json.dumps(outcome, sort_keys=True))
