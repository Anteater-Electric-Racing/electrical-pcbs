"""Minimal Notion REST client (standard library only) plus property helpers."""
import json
import time
import urllib.error
import urllib.request

API = "https://api.notion.com/v1"
VERSION = "2022-06-28"


def _norm_id(i):
    return (i or "").replace("-", "").lower()


class Notion:
    def __init__(self, token, dry_run=False, writable_databases=()):
        self.token = token
        self.dry_run = dry_run
        self.writes = []  # (action, target, payload) for dry runs and summaries
        # Hard guard: only these databases may be read or written, and only pages
        # read from (or created in) them may be updated or commented on.
        self.writable = {_norm_id(d) for d in writable_databases if d}
        self.known_pages = set()

    def _allow_db(self, database_id):
        if _norm_id(database_id) not in self.writable:
            raise PermissionError(f"Refusing to touch Notion database {database_id}: not in the allowed list")

    def _allow_page(self, page_id):
        if _norm_id(page_id) not in self.known_pages:
            raise PermissionError(f"Refusing to modify Notion page {page_id}: not a row of an allowed database")

    def _call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        for attempt in range(6):
            req = urllib.request.Request(
                API + path,
                data=data,
                method=method,
                headers={
                    "Authorization": "Bearer " + self.token,
                    "Notion-Version": VERSION,
                    "Content-Type": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    time.sleep(0.34)  # stay under Notion's ~3 requests/second
                    return json.loads(r.read() or b"{}")
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and attempt < 5:
                    time.sleep(float(e.headers.get("Retry-After", 2 ** attempt)))
                    continue
                raise RuntimeError(f"Notion {method} {path}: {e.code} {e.read()[:500]!r}")
        raise RuntimeError("unreachable")

    def query(self, database_id):
        self._allow_db(database_id)
        pages, cursor = [], None
        while True:
            body = {"page_size": 100}
            if cursor:
                body["start_cursor"] = cursor
            res = self._call("POST", f"/databases/{database_id}/query", body)
            for page in res["results"]:
                parent = page.get("parent", {})
                if parent.get("type") == "database_id" and _norm_id(parent.get("database_id")) in self.writable:
                    self.known_pages.add(_norm_id(page["id"]))
            pages += res["results"]
            if not res.get("has_more"):
                return pages
            cursor = res["next_cursor"]

    def _write(self, action, target, method, path, body):
        self.writes.append((action, target, body))
        if self.dry_run:
            return {"id": f"dry-run-{len(self.writes)}"}
        return self._call(method, path, body)

    def create(self, database_id, props, label=""):
        self._allow_db(database_id)
        page = self._write("create", label, "POST", "/pages",
                           {"parent": {"database_id": database_id}, "properties": props})
        self.known_pages.add(_norm_id(page["id"]))
        return page

    def update(self, page_id, props, label=""):
        self._allow_page(page_id)
        return self._write("update", label, "PATCH", f"/pages/{page_id}", {"properties": props})

    def archive(self, page_id, label=""):
        self._allow_page(page_id)
        return self._write("archive", label, "PATCH", f"/pages/{page_id}", {"archived": True})

    def comment(self, page_id, rich_text, label=""):
        self._allow_page(page_id)
        return self._write("comment", label, "POST", "/comments",
                           {"parent": {"page_id": page_id}, "rich_text": rich_text})


# ---- property builders -------------------------------------------------------
def _rt(s):
    s = s or ""
    return [{"type": "text", "text": {"content": s[i:i + 2000]}} for i in range(0, len(s), 2000)]


def title(s): return {"title": _rt(s)}
def text(s): return {"rich_text": _rt(s)}
def url(s): return {"url": s or None}
def number(n): return {"number": n}
def select(s): return {"select": {"name": s} if s else None}
def status(s): return {"status": {"name": s}}
def checkbox(b): return {"checkbox": bool(b)}
def relation(ids): return {"relation": [{"id": i} for i in ids]}
def date(iso): return {"date": {"start": iso}}


def mention(user_id): return {"type": "mention", "mention": {"user": {"id": user_id}}}
def plain_rt(s): return {"type": "text", "text": {"content": s[:2000]}}


# ---- property readers --------------------------------------------------------
def people_names(page, name):
    """Names in a people property (needs the connection's "Read user information" capability)."""
    p = page.get("properties", {}).get(name) or {}
    return [u.get("name") or "(unknown)" for u in p.get("people", [])]


def read(page, name):
    """Plain value of a property: str for text-like, list for people/relation."""
    p = page.get("properties", {}).get(name)
    if not p:
        return None
    t = p["type"]
    if t in ("title", "rich_text"):
        return "".join(x.get("plain_text", x.get("text", {}).get("content", "")) for x in p[t])
    if t in ("url", "email", "phone_number", "number", "checkbox"):
        return p[t]
    if t in ("select", "status"):
        return (p[t] or {}).get("name")
    if t == "people":
        return [u["id"] for u in p[t]]
    if t == "relation":
        return [r["id"] for r in p[t]]
    if t == "date":
        return (p[t] or {}).get("start")
    return None
