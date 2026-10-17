# Northstar

A polished, responsive deployment dashboard mock with a working JSON API and persistent SQLite database. The demo comes pre-seeded with projects, deployments, and sample operational metrics.

## Run locally

Requires Python 3.13 or newer. No third-party Python packages are needed.

```powershell
python server.py
```

Open http://localhost:8000. Data is stored in `data/northstar.db` by default. Set `DATABASE_PATH` to move the database file.

Or run the container stack:

```powershell
docker compose up --build
```

## API

- `GET /api/health` — process and database health
- `GET /api/overview` — dashboard metrics, projects, and latest deployments
- `GET /api/projects` — projects
- `POST /api/projects` — create `{ "name": "My API", "repo": "team/my-api", "branch": "main" }`
- `GET /api/deployments` — deployment history
- `POST /api/deployments` — queue `{ "project_id": 1, "version": "v1.2.0", "environment": "Preview" }`

## DevOps cycle

1. Create a feature branch and open a pull request.
2. GitHub Actions compiles the API and builds the Docker image on every push and pull request.
3. Merge to `main` after review; connect the repository to Render and use the included `render.yaml` blueprint to deploy.
4. Render checks `/api/health`, serves the container, and keeps SQLite data on its mounted persistent disk.
5. Watch deployment health and logs, then roll back to the prior image if the health check fails.

## Production notes

This is a self-contained demo. The dashboard metrics and first-run records are sample data, and the deployment endpoint queues records without connecting to a real build system. SQLite is appropriate for this single-service mock; replace it with managed PostgreSQL and add authentication, secrets management, migrations, and real build runners before production use. Render deployment requires a connected Render account and a Git remote with this project pushed to it.

