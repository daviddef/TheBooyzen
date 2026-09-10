#!/usr/bin/env python3
"""A local sink so the browser can hand harvested rows straight to disk.
The FamilySearch search API refuses curl (bot protection) but works from a page
context, so the harvest runs in the browser and POSTs here. CORS wide open on
purpose: it listens on loopback only and exists for the length of one harvest."""
import http.server, json, os, sys

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "harvest")
os.makedirs(OUT, exist_ok=True)

class H(http.server.BaseHTTPRequestHandler):
    def _cors(self, code=200):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
    def do_OPTIONS(self): self._cors(204)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        try:
            d = json.loads(body)
            name = "".join(c for c in d.get("file", "drop") if c.isalnum() or c in "._-")
            path = os.path.join(OUT, name + ".json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(d.get("rows", []), f, ensure_ascii=False)
            msg = {"ok": True, "wrote": path, "n": len(d.get("rows", []))}
        except Exception as e:
            msg = {"ok": False, "err": str(e)}
        self._cors()
        self.wfile.write(json.dumps(msg).encode())
    def log_message(self, *a): pass

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8799
print("sink on", port, "->", OUT, flush=True)
http.server.HTTPServer(("127.0.0.1", port), H).serve_forever()
