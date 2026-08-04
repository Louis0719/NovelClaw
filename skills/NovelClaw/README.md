# NovelClaw

<div align="center">
  <p>
    <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
    <img src="https://img.shields.io/badge/FastAPI-Writing%20Workspace-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI writing workspace">
    <img src="https://img.shields.io/badge/Scope-Long--Form%20Fiction-F97316?style=for-the-badge" alt="Long-form fiction">
    <img src="https://img.shields.io/badge/Mode-Chapter%20Control%20%26%20Memory-0f766e?style=for-the-badge" alt="Chapter control and memory">
    <img src="https://img.shields.io/badge/Release-GitHub%20Safe-f59e0b?style=for-the-badge" alt="GitHub-safe release">
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-111827?style=for-the-badge" alt="MIT License"></a>
  </p>

  <h3>✨ Writing a long novel? The scariest part isn't running out of ideas — it's forgetting what you wrote.</h3>


  <p>
    💡 NovelClaw is the first long-form memory tool designed for fiction authors — it <strong>remembers every character detail, plot thread, and power system</strong> across all your chapters, so your 1M-word story stays consistent from start to finish.
  </p>

  <p>
    <b>🌐 Try it online:</b> <a href="https://colong-idea-studio.cloud/">colong-idea-studio.cloud</a>
  </p>

  <p>
    <b>🚀 Start locally now:</b> <code>.\START_LOCAL.bat</code>
  </p>

  <p>
    <a href="https://colong-idea-studio.cloud/"><img src="https://img.shields.io/badge/Live%20Platform-Open%20Now-0f766e?style=flat-square&logo=googlechrome&logoColor=white" alt="Live platform"></a>
    <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Chinese-README-ef4444?style=flat-square" alt="Chinese README"></a>
    <a href="RUN_LOCAL_WEB.md"><img src="https://img.shields.io/badge/Local%20Run-Startup%20Guide-f59e0b?style=flat-square&logo=readthedocs&logoColor=white" alt="Local run guide"></a>
    <a href="DEPLOYMENT.md"><img src="https://img.shields.io/badge/Deployment-Server%20Notes-0f766e?style=flat-square" alt="Deployment guide"></a>
    <a href="WHAT_IS_SAFE_FOR_GITHUB.md"><img src="https://img.shields.io/badge/GitHub%20Safe-Checklist-111827?style=flat-square" alt="GitHub safety"></a>
  </p>

  <p>
    <a href="#overview">Overview</a> |
    <a href="#visual-tour">Visual Tour</a> |
    <a href="#why-it-stands-out">Why It Stands Out</a> |
    <a href="#workflow">Workflow</a> |
    <a href="#quick-start">Quick Start</a> |
    <a href="#claw-mode-guide">Claw Mode Guide</a> |
    <a href="#architecture">Architecture</a> |
    <a href="#runtime-artifacts">Runtime Artifacts</a>
  </p>
</div>

> 🚀 **Local Preview**
> 👀 Enter from **`http://127.0.0.1:8010/select-mode`**, then continue into **`http://127.0.0.1:8012/dashboard`** for the main NovelClaw workspace.

> 🌐 **Live Platform**
> Visit **[colong-idea-studio.cloud](https://colong-idea-studio.cloud/)** if you want the fastest online entry point.

## Overview 🌟

https://github.com/user-attachments/assets/f768395f-0d6e-471f-826d-62aed266fd0e

<p align="center">
  <sub>Demo showcase of the NovelClaw workspace.</sub>
</p>

Long-form fiction authors hit three walls:

**Wall 1: Character Drift** — By Chapter 80, the protagonist's personality from Chapter 3 is completely gone. Readers notice immediately.

**Wall 2: Plot Threads Unresolved** — You planted 15 hooks in the opening. At the finale, you've forgotten 10 of them. Comments say "author never paid off this subplot."

**Wall 3: Power System Collapse** — The Foundation Establishment realm can defeat the Golden Core realm. Then the Golden Core realm loses to the Qi Refining realm. Readers call you "mathematically challenged."

NovelClaw solves all three. It turns long-form writing into ongoing sessions, persistent memory, and chapter-level control — so you can look up any character detail, review any plot thread, or check any power rule at any point in your story.

- 📚 long-form fiction, serial writing, and chapter-by-chapter continuation
- 🧠 <strong>Memory Bank</strong>: store character profiles, world rules, plot notes — searchable across all chapters
- 📋 <strong>Storyboard</strong>: visual map of all plot threads, resolved or still open
- ⚔️ <strong>World Interface</strong>: lock in power systems and realm hierarchies so AI output respects them
- 🤝 human-in-the-loop writing workflows with persistent control surfaces
- 🔍 observable runs with logs, progress traces, chapters, downloads, and review pages

<table>
  <tr>
    <td width="33%" valign="top">
      <h3>🧠 Memory Bank</h3>
      <p>Store every character detail, world rule, and plot note in an editable memory bank. Search it in 3 seconds at any chapter — no need to scroll back to the beginning.</p>
    </td>
    <td width="33%" valign="top">
      <h3>📋 Storyboard Thread Tracker</h3>
      <p>Visualize every plot hook you've planted. See at a glance which ones are resolved and which are still dangling — no more forgotten payoffs at the finale.</p>
    </td>
    <td width="33%" valign="top">
      <h3>⚔️ Power System Lock</h3>
      <p>Write your realm hierarchy and power rules into the World interface. The AI follows them automatically — no Foundation-beats-Golden-Core inconsistencies.</p>
    </td>
  </tr>
</table>

## Visual Tour 👀

<p align="center">
  <img src="docs/readme-triptych-en.png" alt="From clean entry to sustained drafting to inspectable chapter control" width="100%">
</p>

NovelClaw is built around a simple claim: long-form writing quality improves when drafting, review, and memory control are treated as a continuing workspace rather than a one-pass generation event. ✨

## Why It Stands Out ✨

<p align="center">
  <img src="docs/dynamic-memory.png" alt="NovelClaw workflow across chapters, memory, and inspectable outputs" width="100%">
</p>

| Common writing pain | NovelClaw solution |
|---|---|
| "I forgot what happened in earlier chapters" | Memory Bank persists across all chapters — look up Ch.3 character details from Ch.180 |
| Planted 15 plot hooks, forgot 10 at the finale | Storyboard visualizes every thread — resolved or dangling,一眼看清 |
| Power system falls apart mid-story | World Interface locks in realm rules — AI auto-respects them |
| No idea where AI changed things | Run Inspection exposes worker.log + progress.log — every edit transparent |
| Switching tools means losing all your data | Local-first: your data stays on your machine, no platform lock-in |

### NovelClaw In Practice 🧠

- 📝 conversation sessions remain available as active writing context
- 📌 chapter output, progress traces, and downloads stay inspectable throughout a run
- 👤 world, character, style, and manuscript surfaces remain available for revision and continuation
- 🔁 Portal and MultiAgent can assist with entry and preparation, but the main long-form control surface remains NovelClaw

## Workflow 🔄

<table>
  <tr>
    <td width="25%" valign="top">
      <h4>1. Enter</h4>
      <p>Start from the public entry at <code>/select-mode</code> so the bundle remains cleanly separated from the old private auth flow.</p>
    </td>
    <td width="25%" valign="top">
      <h4>2. Prepare</h4>
      <p>If needed, use the support layers for provider setup or faster idea refinement before moving into the main writing workspace.</p>
    </td>
    <td width="25%" valign="top">
      <h4>3. Draft</h4>
      <p>Work inside NovelClaw to continue sessions, monitor runs, inspect chapter output, and steer manuscript development.</p>
    </td>
    <td width="25%" valign="top">
      <h4>4. Review</h4>
      <p>Use manuscript, storyboard, world, character, style, and memory-bank surfaces to keep the project coherent as it grows.</p>
    </td>
  </tr>
</table>

## Best Use Cases 🎯

- 📖 chapter-based long-form fiction and serialized writing workflows
- 🧠 writing projects that need continuity tracking rather than one-pass output
- 🤝 collaborative or supervised drafting where the author keeps steering the process
- 🧪 engineering and product experiments around inspectable long-form writing systems

## Quick Start 🚀

<details open>
<summary><b>🐳 Option A: Docker Deployment (Recommended)</b></summary>

💻 Quick start with Docker:

**Windows:**
```batch
.\docker-start.bat
```

**Linux/Mac:**
```bash
chmod +x docker-start.sh
./docker-start.sh
```

**Or manually:**
```bash
# 1. Setup environment files
cp .env.auth-portal.example apps/auth-portal/.env
cp .env.multiagent.example apps/multiagent/.env
cp .env.novelclaw.example apps/novelclaw/.env

# 2. Review .env files. API keys are optional until you run a cloud provider.

# 3. Start services
docker compose up -d
```

🌐 Access URLs:

```text
Portal      http://localhost:8010/select-mode
MultiAgent  http://localhost:8011/dashboard
NovelClaw   http://localhost:8012/dashboard
```

The portal keeps the host you opened (`localhost` or `127.0.0.1`) when it sends you to the workspace ports, so cross-port session cookies keep working in Docker.

✅ Docker benefits:

- no Python environment setup required
- consistent deployment across platforms
- easy to start, stop, and manage services
- data persistence through volumes

📖 See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for detailed Docker deployment guide.
🤖 CLI/agent automation can use the token API in [docs/AGENT_API.md](docs/AGENT_API.md).

</details>

<details>
<summary><b>🌐 Option B: One-Click Local Stack</b></summary>

💻 Recommended on Windows:

```powershell
.\START_LOCAL.bat
```

🌐 Local URLs:

```text
Portal      http://127.0.0.1:8010/select-mode
MultiAgent  http://127.0.0.1:8011/dashboard
NovelClaw   http://127.0.0.1:8012/dashboard
```

✅ Recommended main path:

```text
http://127.0.0.1:8010/select-mode -> http://127.0.0.1:8012/dashboard
```

✅ What this script does:

- stops old listeners on `8010`, `8011`, and `8012`
- writes local `.env` files from safe defaults
- prepares a shared `.venv-shared`
- starts `Portal`, `MultiAgent`, and `NovelClaw`

</details>

<details>
<summary><b>⌨️ Option B: Manual PowerShell Startup</b></summary>

```powershell
.\scripts\setup-local-env.ps1 -Overwrite
.\scripts\bootstrap-shared-venv.ps1
.\scripts\start-all-local.ps1 -UseSharedVenv
```

🛑 Stop everything:

```powershell
.\STOP_LOCAL.bat
```

🛠️ Helpful commands:

```powershell
.\scripts\stop-all-local.ps1
.\scripts\start-all-local.ps1 -UseSharedVenv -RestartExisting
```

</details>

<a id="claw-mode-guide"></a>
## Claw Mode Guide 🛠️

If your goal is to work inside the main NovelClaw writing workspace, the most practical operating path is:

1. Enter the workspace
   Start from `http://127.0.0.1:8010/select-mode`, choose `NovelClaw`, and continue into `http://127.0.0.1:8012/dashboard`.
1. Configure models first
   Open `/console/models`, save an API key for an available provider, or add a custom provider if you do not want to use the default list. If no provider is configured, the chat workspace will remind you to finish this step first.
1. Start a writing session
   Open `/console/chat`, choose a provider, and submit an initial premise, tone, cast, or writing task. NovelClaw will open an active conversation thread, continue asking for refinement when needed, and let you hand the brief off to formal creation when the session is ready.
1. Track the active run
   Open `/console/tasks` or the linked job detail page to inspect run status, `worker.log`, `progress.log`, chapter output, and downloadable artifacts while the writing process is running.
1. Review and continue
   Use `/console/manuscript/read` for chapter reading, `/console/storyboard` for outline and plot structure, and `/console/memory/banks` for memory inspection or edits. Then return to `/console/chat` to continue the same session instead of starting from scratch.

In short: `Models` configures the writing stack, `Chat` starts and steers the session, `Runs` exposes execution state, and `Manuscript / Storyboard / Memory Banks` provide the main continuation surfaces after generation begins.

## What You Get 🎁

<table>
  <tr>
    <td width="50%" valign="top">
      <h3>🎨 Workspace Capabilities</h3>
      <ul>
        <li>ongoing writing sessions</li>
        <li>manuscript and storyboard views</li>
        <li>world, character, and style surfaces</li>
        <li>editable memory-bank tools</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h3>🔍 Inspectable Output</h3>
      <ul>
        <li>worker logs and progress traces</li>
        <li>chapter output and downloadable artifacts</li>
        <li>job detail and run review surfaces</li>
        <li>GitHub-safe deployment references</li>
      </ul>
    </td>
  </tr>
</table>

## Architecture 🧠

<p align="center">
  <img src="docs/workflow.png" alt="NovelClaw workflow diagram" width="94%">
</p>

The architecture links public entry, writing sessions, run execution, manuscript review, and memory-aware continuation into one inspectable loop, so the workspace can support longer projects without collapsing into a single opaque prompt interaction.

## Runtime Artifacts 📦

The most useful paths for inspecting NovelClaw are:

```text
apps/novelclaw/local_web_portal/data/app.db
apps/novelclaw/local_web_portal/runs/<run_id>/
```

Representative files inside a run directory:

```text
status.json
worker.log
progress.log
output.txt
chapters/
```

Representative `progress.log` events:

| Event | Meaning |
|---|---|
| `global_outline` | Global outline persisted |
| `chapter_outline_ready` | Chapter outlines prepared |
| `chapter_plan` | Current chapter writing plan |
| `chapter_length_plan` | Chapter target and inferred source |
| `memory_snapshot` | Memory snapshot refreshed |
| `character_setting` / `world_setting` | Setting memory written back |

<details>
<summary><b>Repository Layout</b></summary>

```text
.
|-- apps/
|   |-- auth-portal/       # public entry layer
|   |-- multiagent/        # optional fast ideation layer
|   `-- novelclaw/         # main writing workspace
|-- scripts/               # local bootstrap / start / stop helpers
|-- docs/                  # screenshots and operator notes
|-- infra/
|   |-- nginx/             # reverse-proxy example
|   |-- systemd/           # service unit examples
|   `-- env/               # safe env templates only
`-- state_snapshots/       # intentionally cleared for public-safe release
```

</details>

<details>
<summary><b>Deployment Notes</b></summary>

- upload source, docs, and infrastructure references only
- keep real `.env` values and secrets outside the repository
- do not commit runtime databases, restored snapshots, or local keys after running the stack
- treat `/claw/` as the main product route and `/select-mode` as its public entry

See [DEPLOYMENT.md](DEPLOYMENT.md), [docs/DEPLOYMENT.zh-CN.md](docs/DEPLOYMENT.zh-CN.md), [RUN_LOCAL_WEB.md](RUN_LOCAL_WEB.md), [docs/LOCAL_RUN.zh-CN.md](docs/LOCAL_RUN.zh-CN.md), and [WHAT_IS_SAFE_FOR_GITHUB.md](WHAT_IS_SAFE_FOR_GITHUB.md) for operator-focused details.

</details>

## 🙇‍ Thanks
[Linux.do](https://linux.do/)

## Documentation 📚

- 🇨🇳 Chinese README: [README.zh-CN.md](README.zh-CN.md)
- 🌐 Local run guide: [RUN_LOCAL_WEB.md](RUN_LOCAL_WEB.md)
- 🌐 本地运行指南: [docs/LOCAL_RUN.zh-CN.md](docs/LOCAL_RUN.zh-CN.md)
- 🛠️ Deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- 🛠️ 部署说明: [docs/DEPLOYMENT.zh-CN.md](docs/DEPLOYMENT.zh-CN.md)
- 🔐 GitHub safety notes: [WHAT_IS_SAFE_FOR_GITHUB.md](WHAT_IS_SAFE_FOR_GITHUB.md)
- ⚖️ License: [MIT](LICENSE)
