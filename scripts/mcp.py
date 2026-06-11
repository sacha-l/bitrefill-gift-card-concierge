#!/usr/bin/env python3
"""Tiny Streamable-HTTP MCP client for the Bitrefill hosted MCP.

Usage:
  python3 scripts/mcp.py list
  python3 scripts/mcp.py call <tool-name> '<json-args>'

Reads BITREFILL_API_KEY from .env. Stateless server (no session id needed).
"""
import json
import os
import sys
import urllib.request


def load_key() -> str:
    key = os.environ.get("BITREFILL_API_KEY")
    if not key:
        with open(os.path.join(os.path.dirname(__file__), "..", ".env")) as f:
            for line in f:
                line = line.strip()
                if line.startswith("BITREFILL_API_KEY="):
                    key = line.split("=", 1)[1]
    if not key:
        sys.exit("BITREFILL_API_KEY not found (.env or env)")
    return key


def rpc(method: str, params: dict, rid: int = 1) -> dict:
    url = f"https://api.bitrefill.com/mcp/{load_key()}"
    body = json.dumps({"jsonrpc": "2.0", "id": rid, "method": method, "params": params}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "bitrefill-dryrun/0.1",
        },
    )
    with urllib.request.urlopen(req) as resp:
        raw = resp.read().decode()
    # Response is SSE: lines like "data: {...}". Grab the last data payload.
    payloads = [ln[len("data: "):] for ln in raw.splitlines() if ln.startswith("data: ")]
    if not payloads:
        return {"_raw": raw}
    return json.loads(payloads[-1])


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "list":
        out = rpc("tools/list", {})
        for t in out.get("result", {}).get("tools", []):
            print(f"- {t['name']}: {t.get('description','')[:100]}")
    elif cmd == "call":
        tool = sys.argv[2]
        args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        out = rpc("tools/call", {"name": tool, "arguments": args})
        print(json.dumps(out, indent=2))
    elif cmd == "raw":
        # raw <method> <json-params>
        method = sys.argv[2]
        params = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        print(json.dumps(rpc(method, params), indent=2))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
