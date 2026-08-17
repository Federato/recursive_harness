"""Client for ISO's live Rating-as-a-Service endpoint. Standard library only.

Phase 2 is *"run the same submission through the engine in `strict-erc` mode and
through ISO's own service, and compare. **Any difference is our defect until
proven otherwise.**"* This is the half that talks to ISO.

**No third-party dependency.** A working client already exists in
`C:\\Projects\\Will_Dan_Collab_dev` and uses `httpx`; the protocol is OAuth 2.0
client credentials followed by a JSON POST, which `urllib` does without adding a
dependency to a project that has none.

Configuration comes from the environment, never from a file in this repository:

    RAAS_ACCESS_TOKEN_URL   the OAuth token endpoint
    RAAS_API_ENDPOINT       the rate endpoint
    RAAS_CLIENT_ID          }
    RAAS_CLIENT_SECRET      } client-credentials grant
    RAAS_ORG_ID             } the authorization block in a request header
    RAAS_SHIP_ID            }
    RAAS_USE_BASIC_AUTH     "true" to send the client id/secret as HTTP Basic
    RAAS_VERIFY_TLS         "false" only ever for a local proxy

**Nothing here logs a secret.** Errors quote the status and the response body,
which ISO's gateway does not echo credentials into, and the token itself is
never printed.
"""
from __future__ import annotations

import base64
import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

#: Refresh a token this many seconds before it actually expires.
REFRESH_MARGIN = 60.0

REQUIRED = ("RAAS_ACCESS_TOKEN_URL", "RAAS_API_ENDPOINT", "RAAS_CLIENT_ID",
            "RAAS_CLIENT_SECRET")

#: Jurisdictions this subscription does not cover. **The boundary is on the ISO
#: account, not on the engine** -- these still rate offline, they simply have no
#: external answer to be compared against, so a comparison run leaves them out
#: rather than reporting a permanent failure.
#:
#: `PR` -- RAaS answers `401 "Permission is not granted to GL PR for rating.
#: Please check subscription."` Recorded as OI-86 and **closed by decision on
#: 2026-08-13: the entitlement is not available to this project.** Puerto Rico
#: therefore ships with no external confirmation of any kind (it has no stored
#: priced example either -- OI-79), and that must be said wherever its premium
#: is presented rather than left for a reader to discover.
NO_ISO = frozenset({"PR"})


class RaaSError(RuntimeError):
    """The service refused, or answered with something unusable.

    **Carries the request as well as the response.** A 400 whose payload has
    been thrown away cannot be investigated, cannot be reproduced, and cannot be
    sent to ISO -- and ISO's 400s are not always about us: on 2026-08-17 the
    body turned out to be ISO's own rule engine failing to find a row in ISO's
    own table. That is reportable, and reporting it needs the exact request.
    """

    def __init__(self, message: str, status: int | None = None,
                 body: str = "", payload: dict | None = None, url: str = ""):
        super().__init__(message)
        self.status = status
        self.body = body
        self.payload = payload
        self.url = url


def load_env(path: str | Path | None = None) -> dict:
    """Read `KEY=value` lines into the process environment if not already set.

    Existing environment variables win, so a shell export always beats a file.
    The file lives outside this repository -- credentials are never committed.
    """
    if path is None:
        path = os.environ.get("RAAS_ENV_FILE", r"C:\Projects\Will_Dan_Collab_dev\.env")
    p = Path(path)
    if not p.exists():
        return {}
    loaded = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        loaded[k] = v
        os.environ.setdefault(k, v)
    return loaded


def _truthy(name: str, default: bool) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _ctx() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    if not _truthy("RAAS_VERIFY_TLS", True):
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


class RaaS:
    """Authenticate once, rate many. Retries a rotated token exactly once."""

    def __init__(self, timeout: float = 120.0):
        load_env()
        missing = [k for k in REQUIRED if not os.environ.get(k)]
        if missing:
            raise RaaSError(
                f"missing credentials: {', '.join(missing)}. Set them in the "
                f"environment or point RAAS_ENV_FILE at a file that does.")
        self.token_url = os.environ["RAAS_ACCESS_TOKEN_URL"]
        self.endpoint = os.environ["RAAS_API_ENDPOINT"]
        self.org_id = os.environ.get("RAAS_ORG_ID", "")
        self.ship_id = os.environ.get("RAAS_SHIP_ID", "")
        self.timeout = timeout
        self._token = None
        self._expires = 0.0
        self.calls = 0

    # ------------------------------------------------------------------ auth

    def _fetch_token(self) -> None:
        data = {"grant_type": "client_credentials"}
        headers = {"Content-Type": "application/x-www-form-urlencoded",
                   "Accept": "application/json"}
        cid = os.environ["RAAS_CLIENT_ID"]
        secret = os.environ["RAAS_CLIENT_SECRET"]
        if _truthy("RAAS_USE_BASIC_AUTH", False):
            basic = base64.b64encode(f"{cid}:{secret}".encode()).decode()
            headers["Authorization"] = f"Basic {basic}"
        else:
            data["client_id"] = cid
            data["client_secret"] = secret
        if os.environ.get("RAAS_SCOPE"):
            data["scope"] = os.environ["RAAS_SCOPE"]

        req = urllib.request.Request(
            self.token_url, data=urllib.parse.urlencode(data).encode(),
            headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout,
                                        context=_ctx()) as r:
                body = json.loads(r.read())
        except urllib.error.HTTPError as exc:
            raise RaaSError(
                f"token endpoint returned {exc.code}: "
                f"{exc.read()[:300].decode('utf-8', 'replace')}") from None
        except urllib.error.URLError as exc:
            raise RaaSError(f"cannot reach the token endpoint: {exc.reason}") from None

        tok = body.get("access_token")
        if not tok:
            raise RaaSError(f"no access_token in the response: {sorted(body)}")
        self._token = tok
        self._expires = time.monotonic() + float(body.get("expires_in", 3600))

    def token(self, force: bool = False) -> str:
        if force or self._token is None or \
                time.monotonic() >= self._expires - REFRESH_MARGIN:
            self._fetch_token()
        return self._token

    # ------------------------------------------------------------------ rate

    def prepare(self, payload: dict) -> dict:
        """Fill the authorization block ISO expects, leaving the body alone."""
        out = json.loads(json.dumps(payload))
        hdr = out.setdefault("header", {})
        hdr.setdefault("quoteback", "")
        auth = hdr.setdefault("authorization", {})
        if self.org_id:
            auth.setdefault("orgId", self.org_id)
        if self.ship_id:
            auth.setdefault("shipId", self.ship_id)
        return out

    def rate(self, payload: dict) -> dict:
        """POST one submission and return ISO's parsed response."""
        body = json.dumps(self.prepare(payload)).encode()
        for attempt in (1, 2):
            req = urllib.request.Request(
                self.endpoint, data=body, method="POST",
                headers={"Content-Type": "application/json",
                         "Accept": "application/json",
                         "Authorization": f"Bearer {self.token(force=attempt > 1)}"})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout,
                                            context=_ctx()) as r:
                    self.calls += 1
                    return json.loads(r.read())
            except urllib.error.HTTPError as exc:
                # 4,000 rather than 400: ISO's rule-engine errors name the
                # matrix, the project and the keys that missed, and the useful
                # part is past the first 400 characters.
                text = exc.read()[:4000].decode("utf-8", "replace")
                if exc.code == 401 and attempt == 1:
                    continue                      # token rotated mid-flight
                err = RaaSError(
                    f"rate endpoint returned {exc.code}: {text[:300]}",
                    status=exc.code, body=text, payload=payload,
                    url=self.rate_url)
                capture(err)
                raise err from None
            except urllib.error.URLError as exc:
                raise RaaSError(f"cannot reach the rate endpoint: {exc.reason}",
                                payload=payload, url=self.rate_url) from None
        raise RaaSError("unreachable")


#: Where a failed call is written so a person can pick it up.
FAILED = Path(__file__).resolve().parent.parent / "results" / "failed-calls"


def capture(err: "RaaSError") -> Path | None:
    """Write a failed call to disk: the exact request, and the exact response.

    **Automatic, and on by default.** A 400 that is only a log line has to be
    reproduced before it can be investigated, and by then the payload that
    caused it has usually been regenerated with a different exposure or a
    different date. Written the moment it happens, it is evidence.
    """
    if err.payload is None:
        return None
    try:
        # A RaaS request is {header, body}; SchemeKeys is inside body. Reading
        # it off the top level silently yielded "unknown" for every capture.
        inner = err.payload.get("body") or err.payload
        juris = ((inner.get("SchemeKeys") or {}).get("ProductName")
                 or "unknown").split()[-1]
    except Exception:                                         # noqa: BLE001
        juris = "unknown"
    stamp = time.strftime("%Y%m%dT%H%M%S")
    d = FAILED / f"{stamp}-{juris}-{err.status or 'err'}"
    try:
        d.mkdir(parents=True, exist_ok=True)
        (d / "request.json").write_text(
            json.dumps(err.payload, indent=2), encoding="utf-8")
        (d / "response.txt").write_text(err.body or "", encoding="utf-8")
        note = [
            f"# {juris} - HTTP {err.status}",
            "",
            f"**Sent to** `{err.url}`",
            f"**At** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## What we sent",
            "",
            "`request.json` in this folder, exactly as posted. It can be",
            "re-sent unchanged.",
            "",
            "## What came back",
            "",
            "```",
            (err.body or "")[:1500],
            "```",
            "",
            "## Worth checking before assuming it is ours",
            "",
            "An HTTP 400 from this service is **not always a complaint about",
            "the submission**. On 2026-08-17 three jurisdictions returned a 400",
            "whose body was ISO's own rule engine failing to find a row in",
            "ISO's own table:",
            "",
            "> Matrix: PremOpsSizeOfRiskLossCost, Keys: CW, 502, 50017.",
            "> No results have been found.",
            "",
            "That is reportable to ISO, not a defect in the payload. **Read the",
            "body before concluding whose problem it is.**",
            "",
        ]
        (d / "what-happened.md").write_text("\n".join(note), encoding="utf-8")
        return d
    except Exception:                                         # noqa: BLE001
        return None
