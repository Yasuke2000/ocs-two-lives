"""HTTP client for the ttl-portals build bridge (stdlib only).

Where the bridge is: TTL_BRIDGE_URL (default http://127.0.0.1:25599). The token: TTL_BRIDGE_TOKEN, else the file
TTL_BRIDGE_TOKEN_FILE, else <TTL_LOCAL_DIR>/config/ttl/bridge.token (the local test server, tools/local.sh).
For staging, forward the port first: `kubectl -n ocs-two-lives port-forward deploy/mc 25599:25599` (docs/dev/build-bridge.md).
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


class BridgeError(RuntimeError):
    def __init__(self, status: int, message: str):
        super().__init__(f"bridge {status}: {message}")
        self.status = status


def _token() -> str:
    if os.environ.get("TTL_BRIDGE_TOKEN"):
        return os.environ["TTL_BRIDGE_TOKEN"].strip()
    candidates = []
    if os.environ.get("TTL_BRIDGE_TOKEN_FILE"):
        candidates.append(Path(os.environ["TTL_BRIDGE_TOKEN_FILE"]))
    if os.environ.get("TTL_LOCAL_DIR"):
        candidates.append(Path(os.environ["TTL_LOCAL_DIR"]) / "config" / "ttl" / "bridge.token")
    for path in candidates:
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    return ""


class Bridge:
    def __init__(self, url: str | None = None, token: str | None = None, timeout: float = 90):
        self.url = (url or os.environ.get("TTL_BRIDGE_URL") or "http://127.0.0.1:25599").rstrip("/")
        self.token = token if token is not None else _token()
        self.timeout = timeout
        # Never send bridge traffic through an HTTP proxy: the bridge is local (or port-forwarded).
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def call(self, method: str, path: str, query: dict | None = None, body: dict | None = None) -> dict:
        if not self.token:
            raise BridgeError(0, "no token: set TTL_BRIDGE_TOKEN (or TTL_BRIDGE_TOKEN_FILE / TTL_LOCAL_DIR)")
        url = self.url + "/v1/" + path.lstrip("/")
        if query:
            url += "?" + urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        try:
            with self.opener.open(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                message = json.loads(e.read().decode("utf-8")).get("error", e.reason)
            except Exception:
                message = str(e.reason)
            raise BridgeError(e.code, message) from None
        except urllib.error.URLError as e:
            raise BridgeError(0, f"cannot reach {self.url} ({e.reason}); is the server up with bridge.json enabled, "
                                 "and the port forwarded?") from None

    def get(self, path, **query):
        return self.call("GET", path, query=query)

    def post(self, path, body):
        return self.call("POST", path, body=body)


def encode_job(bp, origin, dim="minecraft:overworld", label="", dry_run=True, updates="quiet", fix_shapes=True) -> dict:
    """A Blueprint as a bridge job: palette + run-length cells (x fastest, then z, then y; -1 = keep)."""
    w, h, l = bp.size
    nbt = getattr(bp, "nbt", {})
    palette, index, runs = [], {}, []
    current, count = None, 0
    for y in range(h):
        for z in range(l):
            for x in range(w):
                state = bp.blocks.get((x, y, z))
                if state is not None and (x, y, z) in nbt:
                    state += nbt[(x, y, z)]  # the bridge parses 'id[props]{nbt}' like /setblock
                if state is None:
                    value = -1
                else:
                    value = index.get(state)
                    if value is None:
                        value = index[state] = len(palette)
                        palette.append(state)
                if value == current:
                    count += 1
                else:
                    if count:
                        runs.append([count, current])
                    current, count = value, 1
    if count:
        runs.append([count, current])
    if not palette:
        raise ValueError("the build sets no blocks")
    return {"dim": dim, "origin": list(origin), "size": [w, h, l], "palette": palette, "rle": runs,
            "dry_run": bool(dry_run), "label": label, "updates": updates, "fix_shapes": bool(fix_shapes)}


def decode_blocks(region: dict, name: str = "export"):
    """A /v1/region?mode=blocks answer as a Blueprint (unloaded cells are left out)."""
    from blueprint import Blueprint
    w, h, l = region["size"]
    bp = Blueprint(name, (w, h, l))
    palette = region["palette"]
    i = 0
    for count, value in region["rle"]:
        if value >= 0:
            state = palette[value]
            for k in range(i, i + count):
                bp.blocks[(k % w, k // (w * l), (k // w) % l)] = state
        i += count
    return bp
