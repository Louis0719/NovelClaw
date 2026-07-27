param(
  [switch]$Overwrite
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$sharedSecretDir = Join-Path $root ".local-dev-secrets"

function To-PosixPath([string]$path) {
  return $path.Replace('\', '/')
}

function To-SqliteUrl([string]$path) {
  return "sqlite:///" + (To-PosixPath $path)
}

function Write-FileIfNeeded([string]$Path, [string]$Content, [switch]$OverwriteExisting) {
  if ((Test-Path $Path) -and -not $OverwriteExisting.IsPresent) {
    Write-Host "[skip] $Path already exists"
    return
  }
  Set-Content -Path $Path -Value $Content -Encoding UTF8
  Write-Host "[ok] wrote $Path"
}

function Get-OrCreateLocalDevSecret([string]$Path, [scriptblock]$Factory) {
  if (Test-Path $Path) {
    return (Get-Content $Path -Raw).Trim()
  }
  $value = & $Factory
  Set-Content -Path $Path -Value $value -Encoding UTF8
  return $value
}

New-Item -ItemType Directory -Force -Path $sharedSecretDir | Out-Null

$sessionSecretPath = Join-Path $sharedSecretDir "session.secret"
$fernetKeyPath = Join-Path $sharedSecretDir "fernet.key"

$sessionSecret = Get-OrCreateLocalDevSecret $sessionSecretPath {
  [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes(([guid]::NewGuid().ToString() + [guid]::NewGuid().ToString())))
}

$fernetKey = Get-OrCreateLocalDevSecret $fernetKeyPath {
  $bytes = New-Object byte[] 32
  [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
  ([Convert]::ToBase64String($bytes) -replace '\+','-' -replace '/','_')
}

$authApp = Join-Path $root "apps\auth-portal\local_web_portal"
$multiApp = Join-Path $root "apps\multiagent\local_web_portal"
$clawApp = Join-Path $root "apps\novelclaw\local_web_portal"

$authDb = Join-Path $authApp "data\app.db"
$multiDb = Join-Path $multiApp "data\app.db"
$clawDb = Join-Path $clawApp "data\app.db"
$multiRuns = Join-Path $multiApp "runs"
$clawRuns = Join-Path $clawApp "runs"

New-Item -ItemType Directory -Force -Path (Join-Path $authApp "data"), (Join-Path $multiApp "data"), (Join-Path $multiApp "runs"), (Join-Path $clawApp "data"), (Join-Path $clawApp "runs") | Out-Null

$authEnv = @"
APP_BASE_URL=http://127.0.0.1:8010
APP_HTTPS_ONLY=0
APP_SESSION_COOKIE_NAME=colong_shared_session
APP_SESSION_COOKIE_DOMAIN=
APP_SESSION_SECRET=$sessionSecret
APP_DATABASE_URL=$(To-SqliteUrl $authDb)
APP_MULTIAGENT_URL=http://127.0.0.1:8011/dashboard
APP_CLAW_URL=http://127.0.0.1:8012/dashboard
APP_PREVIEW_USER_EMAIL=preview@novelclaw.local
WEB_UI_LANGUAGE=zh
"@

$multiEnv = @"
APP_HTTPS_ONLY=0
APP_BASE_PATH=
APP_SESSION_COOKIE_NAME=colong_shared_session
APP_SESSION_COOKIE_DOMAIN=
APP_SESSION_SECRET=$sessionSecret
APP_ENCRYPTION_KEY=$fernetKey
APP_DATABASE_URL=$(To-SqliteUrl $multiDb)
APP_AUTH_DATABASE_URL=$(To-SqliteUrl $authDb)
APP_SHARED_PORTAL_URL=http://127.0.0.1:8010
APP_RUNS_DIR=$(To-PosixPath $multiRuns)
WEB_BUILTIN_PROVIDERS=deepseek
WEB_DEFAULT_PROVIDER=deepseek
WEB_MAX_ITERATIONS=8
WEB_MAX_TOTAL_ITERATIONS=16
WEB_JOB_TIMEOUT_SECONDS=0
WEB_JOB_IDLE_TIMEOUT_SECONDS=0
WEB_STARTUP_RECOVERY_SECONDS=180
WEB_STALE_QUEUED_SECONDS=180
WEB_FAST_MODE=1
WEB_FULL_CYCLE_INTERVAL=3
WEB_CHAPTERS_PER_ITER=1
WEB_MAX_CHAPTER_SUBROUNDS=2
WEB_EVAL_INTERVAL=8
LLM_TIMEOUT_SECONDS=0
LLM_MAX_RETRIES=1
WEB_MEMORY_ONLY_MODE=0
WEB_ENABLE_RAG=1
WEB_ENABLE_STATIC_KB=0
WEB_ENABLE_EVALUATOR=1
VECTOR_DB_PATH=
PYTHONUTF8=1
PYTHONIOENCODING=utf-8
HF_HUB_OFFLINE=0
TRANSFORMERS_OFFLINE=0
HF_HOME=
EMBEDDING_MODEL=none
DISABLE_EMBEDDING_DOWNLOADS=1
"@

$clawEnv = @"
APP_HTTPS_ONLY=0
APP_BASE_PATH=
APP_SESSION_COOKIE_NAME=colong_shared_session
APP_SESSION_COOKIE_DOMAIN=
APP_SESSION_SECRET=$sessionSecret
APP_ENCRYPTION_KEY=$fernetKey
APP_DATABASE_URL=$(To-SqliteUrl $clawDb)
APP_AUTH_DATABASE_URL=$(To-SqliteUrl $authDb)
APP_SHARED_PORTAL_URL=http://127.0.0.1:8010
APP_RUNS_DIR=$(To-PosixPath $clawRuns)
WEB_BUILTIN_PROVIDERS=deepseek
WEB_DEFAULT_PROVIDER=deepseek
WEB_MODELLESS_MODE=0
WEB_EXECUTION_MODE=claw
WEB_CLAW_MAX_STEPS=12
WEB_MAX_ITERATIONS=8
WEB_MAX_TOTAL_ITERATIONS=16
WEB_JOB_TIMEOUT_SECONDS=0
WEB_JOB_IDLE_TIMEOUT_SECONDS=0
WEB_STARTUP_RECOVERY_SECONDS=180
WEB_STALE_QUEUED_SECONDS=180
WEB_FAST_MODE=1
WEB_FULL_CYCLE_INTERVAL=3
WEB_CHAPTERS_PER_ITER=1
WEB_MAX_CHAPTER_SUBROUNDS=2
WEB_EVAL_INTERVAL=8
LLM_TIMEOUT_SECONDS=0
LLM_MAX_RETRIES=1
WEB_MEMORY_ONLY_MODE=0
WEB_ENABLE_RAG=1
WEB_ENABLE_STATIC_KB=0
WEB_ENABLE_EVALUATOR=1
VECTOR_DB_PATH=
PYTHONUTF8=1
PYTHONIOENCODING=utf-8
HF_HUB_OFFLINE=0
TRANSFORMERS_OFFLINE=0
HF_HOME=
EMBEDDING_MODEL=none
DISABLE_EMBEDDING_DOWNLOADS=1
MIN_CHAPTER_CHARS=1200
MAX_CHAPTER_CHARS=4000
TEMPERATURE=0.8
MAX_TOKENS=4096
CONTEXT_MAX_CHARS=12000
RECENT_CONTEXT_ITEMS=8
TURNING_POINT_ENABLED=1
"@

Write-FileIfNeeded -Path (Join-Path $authApp ".env") -Content $authEnv -OverwriteExisting:$Overwrite
Write-FileIfNeeded -Path (Join-Path $multiApp ".env") -Content $multiEnv -OverwriteExisting:$Overwrite
Write-FileIfNeeded -Path (Join-Path $clawApp ".env") -Content $clawEnv -OverwriteExisting:$Overwrite
