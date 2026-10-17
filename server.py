from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import json
import os
import sqlite3
from datetime import datetime, timezone

ROOT = Path(__file__).parent
DB_PATH = os.environ.get("DATABASE_PATH", str(ROOT / "data" / "northstar.db"))
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT NOT NULL, repo TEXT NOT NULL, branch TEXT NOT NULL, status TEXT NOT NULL, updated TEXT NOT NULL, color TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS deployments (id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL, version TEXT NOT NULL, environment TEXT NOT NULL, status TEXT NOT NULL, created TEXT NOT NULL, duration TEXT NOT NULL, FOREIGN KEY(project_id) REFERENCES projects(id));
        """)
        if conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
            projects = [
                ("Atlas API", "northstar/atlas-api", "main", "Healthy", "2 min ago", "violet"),
                ("Orbit Web", "northstar/orbit-web", "main", "Healthy", "18 min ago", "blue"),
                ("Pulse Worker", "northstar/pulse-worker", "develop", "Building", "Just now", "orange"),
                ("Beacon SDK", "northstar/beacon-sdk", "main", "Healthy", "1 hr ago", "green"),
            ]
            conn.executemany("INSERT INTO projects(name,repo,branch,status,updated,color) VALUES(?,?,?,?,?,?)", projects)
            deployments = [
                (1,"v2.8.1","Production","Success","2026-10-17T09:42:00Z","1m 24s"),
                (2,"v1.14.0","Production","Success","2026-10-17T09:26:00Z","58s"),
                (3,"v0.9.7","Preview","Building","2026-10-17T09:44:00Z","—"),
                (4,"v3.2.4","Production","Success","2026-10-17T08:31:00Z","2m 06s"),
                (1,"v2.8.0","Production","Success","2026-10-17T08:05:00Z","1m 19s"),
            ]
            conn.executemany("INSERT INTO deployments(project_id,version,environment,status,created,duration) VALUES(?,?,?,?,?,?)", deployments)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def send(self, status, body, content_type="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else (json.dumps(body).encode() if content_type.startswith("application/json") else body.encode())
        self.send_response(status); self.send_header("Content-Type", content_type); self.send_header("Content-Length", str(len(data))); self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Access-Control-Allow-Headers", "Content-Type"); self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS"); self.end_headers(); self.wfile.write(data)
    def do_OPTIONS(self): self.send(204, b"")
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health": return self.send(200, {"status":"ok","database":"connected"})
        if path == "/api/overview":
            with db() as conn:
                projects = [dict(x) for x in conn.execute("SELECT * FROM projects ORDER BY id")]
                deploys = [dict(x) for x in conn.execute("SELECT d.*,p.name AS project FROM deployments d JOIN projects p ON p.id=d.project_id ORDER BY d.id DESC LIMIT 8")]
            return self.send(200,{"projects":projects,"deployments":deploys,"metrics":{"successRate":"99.8%","avgBuild":"1m 42s","activeDeployments":1,"totalProjects":len(projects)}})
        if path == "/api/projects":
            with db() as conn: return self.send(200,[dict(x) for x in conn.execute("SELECT * FROM projects ORDER BY id")])
        if path == "/api/deployments":
            with db() as conn: return self.send(200,[dict(x) for x in conn.execute("SELECT d.*,p.name AS project FROM deployments d JOIN projects p ON p.id=d.project_id ORDER BY d.id DESC")])
        file = ROOT / ("index.html" if path == "/" else path.lstrip("/"))
        if not file.resolve().is_relative_to(ROOT.resolve()) or not file.is_file(): return self.send(404,{"error":"Not found"})
        types={".html":"text/html; charset=utf-8",".css":"text/css; charset=utf-8",".js":"text/javascript; charset=utf-8",".svg":"image/svg+xml"}
        self.send(200,file.read_bytes(),types.get(file.suffix,"application/octet-stream"))
    def do_POST(self):
        path = urlparse(self.path).path
        try: payload=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
        except (ValueError,TypeError): return self.send(400,{"error":"Invalid JSON"})
        if path == "/api/projects":
            name=str(payload.get("name","")).strip(); repo=str(payload.get("repo","")).strip()
            if not name or not repo: return self.send(400,{"error":"Project name and repository are required"})
            with db() as conn:
                cur=conn.execute("INSERT INTO projects(name,repo,branch,status,updated,color) VALUES(?,?,?,'Healthy','Just now','blue')",(name,repo,payload.get("branch","main")))
                row=dict(conn.execute("SELECT * FROM projects WHERE id=?",(cur.lastrowid,)).fetchone())
            return self.send(201,row)
        if path == "/api/deployments":
            try: project_id=int(payload.get("project_id"))
            except (ValueError,TypeError): return self.send(400,{"error":"Choose a project"})
            with db() as conn:
                project=conn.execute("SELECT id FROM projects WHERE id=?",(project_id,)).fetchone()
                if not project: return self.send(404,{"error":"Project not found"})
                cur=conn.execute("INSERT INTO deployments(project_id,version,environment,status,created,duration) VALUES(?,?,?,'Building',?,'—')",(project_id,payload.get("version","v1.0.0"),payload.get("environment","Preview"),datetime.now(timezone.utc).isoformat()))
                row=dict(conn.execute("SELECT d.*,p.name AS project FROM deployments d JOIN projects p ON p.id=d.project_id WHERE d.id=?",(cur.lastrowid,)).fetchone())
            return self.send(201,row)
        self.send(404,{"error":"Not found"})

if __name__ == "__main__":
    init_db()
    port=int(os.environ.get("PORT","8000"))
    print(f"Northstar is running on port {port}",flush=True)
    ThreadingHTTPServer(("0.0.0.0",port),Handler).serve_forever()

