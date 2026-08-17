# Local Setup Guide — NovelClaw

A focused walkthrough for running the three services locally on Windows / macOS / Linux.

> 📖 For high-level quick start, see [`README.md`](README.md) Quick Start.
> 🇨🇳 中文版请见 [`README.zh-CN.md`](README.zh-CN.md)。

---

## 🎯 Which path should I pick?

| Scenario | Recommended path | Why |
|---|---|---|
| First time trying NovelClaw | **Docker** | zero Python setup, all services in one command |
| Windows + actively developing | **PowerShell scripts** | shares `.venv-shared`, faster iteration, no Docker overhead |
| Linux/macOS + actively developing | **Docker** + manual override | Docker for parity, override ports only if needed |
| Server / production-style deploy | **Docker** | image-based, healthchecks, restart policy |

> If unsure, start with Docker. It costs ~30 seconds to spin up.

---

## 🐳 Path 1: Docker (recommended)

### Windows

```batch
docker-start.bat
```

### macOS / Linux

```bash
chmod +x docker-start.sh
./docker-start.sh
```

### What the script does (in order)

1. Verifies Docker + Docker Compose v2 are installed.
2. Creates `apps/{auth-portal,multiagent,novelclaw}/.env` from `local_web_portal/.env.example` (skips if already present).
3. Runs `docker compose up -d` (detached).
4. Health-checks each service via `/healthz` until ready or timeout.

### 🌐 Access URLs

```text
Portal      http://localhost:8010/select-mode
MultiAgent  http://localhost:8011/dashboard
NovelClaw   http://localhost:8012/dashboard
```

The portal preserves the host you opened (e.g. `localhost` vs `127.0.0.1`) so cross-port session cookies keep working.

### 🛑 Stop the stack

```bash
docker compose down                 # stop + remove containers, keep volumes
docker compose down -v              # nuke data volumes too (DESTRUCTIVE)
```

### 📜 Logs

```bash
docker compose logs -f novelclaw    # tail one service
docker compose logs --tail=200      # last 200 lines of all
```

---

## 💻 Path 2: Windows PowerShell (faster iteration)

For Windows users who want direct Python processes (no Docker overhead):

```powershell
.\START_LOCAL.bat
```

That `.bat` calls four scripts in order:

```text
START_LOCAL.bat
  ├─ scripts\stop-all-local.ps1       # kill anything on :8010/8011/8012
  ├─ scripts\setup-local-env.ps1      # write .env (random session secret + Fernet key)
  ├─ scripts\bootstrap-shared-venv.ps1   # create .venv-shared\ with pinned deps
  └─ scripts\start-all-local.ps1      # launch three uvicorn processes
```

### Manual equivalent

If you want finer control:

```powershell
.\scripts\setup-local-env.ps1 -Overwrite
.\scripts\bootstrap-shared-venv.ps1
.\scripts\start-all-local.ps1 -UseSharedVenv
```

### 🛑 Stop

```powershell
.\STOP_LOCAL.bat
# or just one process:
Get-NetTCPConnection -LocalPort 8012 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

### 🔄 Restart one service

```powershell
# Recycle NovelClaw only (UI for writing workspace)
.\scripts\start-all-local.ps1 -UseSharedVenv -RestartExisting
```

---

## 🔐 Environment files

`docker-start.sh/.bat` and `setup-local-env.ps1` both write `.env` to **two locations** for compatibility:

```text
apps/{app}/.env                     ← primary (matches docker-compose.yml volume)
apps/{app}/local_web_portal/.env    ← legacy mirror (settings.py reads both via load_dotenv chain)
```

`settings.py` resolves them in this order: **local_web_portal/.env** → **parent .env** → env vars → safe defaults. So either location works for local runs.

### What the templates contain

| Service | Notable keys |
|---|---|
| auth-portal | `APP_BASE_URL`, `APP_DATABASE_URL`, `APP_SESSION_SECRET` (auto-generated) |
| multiagent | `APP_AUTH_DATABASE_URL` (points to auth-portal's SQLite), `WEB_DEFAULT_PROVIDER=deepseek` |
| novelclaw | `APP_AGENT_API_KEY`, `APP_AUTH_DATABASE_URL`, `WEB_MODELLESS_MODE=0` |

You only need to add LLM API keys if you actually run a generation. For browsing the UI, defaults are safe.

### 🔑 Rotate session secret

If you want to invalidate all logged-in sessions:

```powershell
# Delete the shared secret file; next start regenerates
Remove-Item .local-dev-secrets\session_secret.txt
.\scripts\start-all-local.ps1 -UseSharedVenv
```

(Containers share the secret via volume mount — Docker users need to clear the named volume.)

---

## 🩺 Health checks

Each service exposes `/healthz`:

```bash
curl -s http://localhost:8010/healthz   # auth-portal
curl -s http://localhost:8011/healthz   # multiagent
curl -s http://localhost:8012/healthz   # novelclaw
```

Expected response:

```json
{"ok": true}
```

`docker-compose.yml` polls these in the background; unhealthy containers are auto-restarted.

---

## 🐞 Troubleshooting

### "Port already in use" on start

```text
[ERROR] bind: address already in use :::8010
```

**Fix:** another process is on port 8010/8011/8012.

```bash
# Linux/macOS
lsof -ti:8010,8011,8012 | xargs kill -9

# Windows PowerShell
.\STOP_LOCAL.bat
```

### `.env.example template not found`

You probably ran `docker-start.sh` from the wrong directory. The script expects to be run from the `NovelClaw/` root.

```bash
cd skills/NovelClaw
./docker-start.sh
```

### "No provider configured" when starting a session

NovelClaw runs in `WEB_MODELLESS_MODE=0` by default — you need to register a provider.

Fix: open `/console/models`, paste an API key for an available provider (e.g. DeepSeek), save. **No restart required.**

### Sessions vanish after restart

`auth-portal` uses a Fernet-encrypted session cookie. If you deleted `.local-dev-secrets/session_secret.txt`, every browser session is invalidated. This is expected behaviour, not a bug.

### Docker container keeps restarting

```bash
docker compose logs novelclaw --tail=50
```

Common causes:

- `.env` missing → re-run `docker-start.sh`
- `APP_SESSION_SECRET` empty in `.env` → templates auto-generate, but if you edited manually, fill it
- Port conflict with host process → see "Port already in use" above

### Reset everything (DESTRUCTIVE — nukes all data)

```bash
# Docker
docker compose down -v
rm -rf apps/*/.env apps/*/local_web_portal/data

# Windows PowerShell
.\STOP_LOCAL.bat
Remove-Item -Recurse -Force .local-dev-secrets, .venv-shared, apps\*\.env, apps\*\local_web_portal\data
```

---

## 📂 Where state lives

| What | Docker location | Local location |
|---|---|---|
| SQLite databases | named volumes (managed by compose) | `apps/*/local_web_portal/data/app.db` |
| Run artifacts | bind-mounted to host `state_snapshots/` | `state_snapshots/` |
| `.env` files | bind-mounted (read-only) | `apps/*/.env` |
| Session secret | named volume `.local-dev-secrets` | `.local-dev-secrets/` |
| Python venv | inside container | `.venv-shared/` (shared across 3 apps) |

**All of these are gitignored.** They never enter your commit history.

---

## 🧪 Verifying a clean install

After `START_LOCAL.bat` finishes:

```powershell
# 1. Three ports should respond
Test-NetConnection 127.0.0.1 -Port 8010   # TcpTestSucceeded : True
Test-NetConnection 127.0.0.1 -Port 8011
Test-NetConnection 127.0.0.1 -Port 8012

# 2. Health endpoints
(Invoke-WebRequest http://127.0.0.1:8010/healthz).Content   # {"ok":true}

# 3. UI loads
start http://127.0.0.1:8010/select-mode
```

If all three pass, you're in business.

---

## ⏭️ Next steps

1. Pick a provider at `/console/models`.
2. Start a session at `/console/chat`.
3. Track progress at `/console/tasks`.
4. Review chapters at `/console/manuscript/read`.

For deeper writing workflow notes, see the **Claw Mode Guide** in [`README.md`](README.md#claw-mode-guide).