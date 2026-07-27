#!/usr/bin/env python3
"""
direct_api_writer.py

Novel Studio direct API writing executor.

Builds an isolated OpenAI-compatible chat/completions request from a chapter
input pack and optionally executes it. Default is dry-run: write request preview
and manifest only, no network call.

Usage:
  python3 scripts/direct_api_writer.py <project-dir> <chapter-id> [options]

Environment:
  NOVEL_STUDIO_API_KEY   API key env var used by default
  NOVEL_STUDIO_BASE_URL  e.g. https://api.openai.com/v1
  NOVEL_STUDIO_MODEL     model name
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib import request, error
import argparse
import json
import os
import re
import subprocess
import sys
import time

DEFAULT_API_KEY_ENV = "NOVEL_STUDIO_API_KEY"
DEFAULT_BASE_URL_ENV = "NOVEL_STUDIO_BASE_URL"
DEFAULT_MODEL_ENV = "NOVEL_STUDIO_MODEL"
SUPPORTED_API = {"openai-completions", "anthropic-messages"}
API_CALL_LOG_FILE = "api-calls.json"
MAX_LOG_ENTRIES = 100
FULL_DETAIL_KEEP = 10
GLOBAL_CONFIG_PATH = Path(__file__).resolve().parent.parent / ".novel-studio" / "global-config.json"


def skill_root() -> Path:
    """Return the Novel Studio skill root directory."""
    return Path(__file__).resolve().parent.parent


@dataclass
class IncludedFile:
    rel: str
    chars: int
    content: str


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# project_config_path removed — model config is now global only.


def providers_from_config(data: dict) -> dict:
    if "providers" in data and isinstance(data["providers"], dict):
        return data["providers"]
    models = data.get("models")
    if isinstance(models, dict) and isinstance(models.get("providers"), dict):
        return models["providers"]
    return {}


def inherited_model_config(provider_id: str, provider: dict, model: dict) -> dict:
    """Return effective model config: provider-level non-secret fields inherited by model."""
    inherited = {
        k: v
        for k, v in provider.items()
        if k not in {"apiKey", "models"}
    }
    inherited["provider"] = provider_id
    inherited.update(model)
    inherited["api"] = model.get("api") or provider.get("api") or inherited.get("api", "")
    inherited["baseUrl"] = (
        model.get("baseUrl")
        or model.get("baseURL")
        or model.get("base_url")
        or provider.get("baseUrl")
        or provider.get("baseURL")
        or provider.get("base_url")
        or inherited.get("baseUrl", "")
    )
    return inherited


def read_global_direct_api() -> tuple[dict | None, Path]:
    """Read the Novel Studio global direct API config."""
    if GLOBAL_CONFIG_PATH.exists():
        try:
            cfg = json.loads(GLOBAL_CONFIG_PATH.read_text(encoding="utf-8"))
            direct = cfg.get("directApi")
            if isinstance(direct, dict):
                return direct, GLOBAL_CONFIG_PATH
        except Exception:
            pass
    return None, GLOBAL_CONFIG_PATH


def _read_full_global_config() -> tuple[dict | None, Path]:
    """Read the full Novel Studio global config (including workMode)."""
    if GLOBAL_CONFIG_PATH.exists():
        try:
            cfg = json.loads(GLOBAL_CONFIG_PATH.read_text(encoding="utf-8"))
            return cfg, GLOBAL_CONFIG_PATH
        except Exception:
            pass
    return None, GLOBAL_CONFIG_PATH


def redact_secrets(value):
    if isinstance(value, dict):
        return {k: ("***" if k.lower() == "apikey" and v else redact_secrets(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_secrets(v) for v in value]
    return value


def safe_rel(root: Path, raw: str) -> Path | None:
    raw = raw.strip().strip("`").strip()
    if not raw or raw.startswith(("http://", "https://")):
        return None
    p = (root / raw).resolve()
    try:
        p.relative_to(root)
    except ValueError:
        return None
    if not p.exists() or not p.is_file():
        return None
    return p


def extract_pack_paths(root: Path, input_pack: Path) -> list[Path]:
    text = read_text(input_pack)
    paths: list[Path] = []
    seen: set[Path] = set()
    for match in re.finditer(r"`([^`]+)`", text):
        p = safe_rel(root, match.group(1))
        if p and p not in seen:
            paths.append(p)
            seen.add(p)
    return paths


def load_included_files(root: Path, paths: list[Path], max_chars_per_file: int, max_total_chars: int) -> list[IncludedFile]:
    included: list[IncludedFile] = []
    total = 0
    for p in paths:
        content = read_text(p)
        if len(content) > max_chars_per_file:
            content = content[:max_chars_per_file] + "\n\n[TRUNCATED by direct_api_writer max_chars_per_file]\n"
        if total + len(content) > max_total_chars:
            remaining = max_total_chars - total
            if remaining <= 0:
                break
            content = content[:remaining] + "\n\n[TRUNCATED by direct_api_writer max_total_chars]\n"
        rel = str(p.relative_to(root))
        included.append(IncludedFile(rel=rel, chars=len(content), content=content))
        total += len(content)
        if total >= max_total_chars:
            break
    return included


def build_messages(chapter_id: str, project_name: str, included: list[IncludedFile], prompt_profile: str, user_instruction: str) -> list[dict]:
    system = f"""你是 Novel Studio 的隔离写作执行模型。\n\n规则：\n- 只使用本次请求中提供的项目资料，不使用任何外部聊天历史或未提供设定。\n- 不擅自改核心设定；缺信息时用最小假设，并在输出末尾用 [待确认] 标注。\n- 写小说正文时，不输出分析过程、任务书或解释，除非用户指令要求。\n- 保持项目风格、人物状态、信息边界和章节 packet 约束。\n- 不把项目管理说明写进正文。\n\n项目：{project_name}\n章节：{chapter_id}\n模式：{prompt_profile}\n"""
    blocks = []
    for item in included:
        blocks.append(f"## FILE: {item.rel}\n\n{item.content}")
    user = f"""# Novel Studio Direct API Input\n\n## Chapter\n{chapter_id}\n\n## User Instruction\n{user_instruction or '请基于以下 input pack 资料，生成本章正文候选稿。'}\n\n## Included Project Files\n\n""" + "\n\n---\n\n".join(blocks) + "\n\n## Output Requirement\n- 默认只输出正文候选稿。\n- 不输出你如何思考。\n- 若资料不足以安全写作，在末尾加 [待确认] 列出缺口。\n"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def chat_completions(base_url: str, api_key: str, payload: dict, timeout: int) -> dict:
    url = base_url.rstrip("/") + "/chat/completions"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body[:2000]}") from e




def anthropic_messages_payload(model: str, messages: list[dict], temperature: float, max_tokens: int) -> dict:
    system = ""
    user_messages = []
    for msg in messages:
        if msg.get("role") == "system":
            system = (system + "\n\n" + msg.get("content", "")).strip()
        else:
            user_messages.append(msg)
    return {
        "model": model,
        "system": system,
        "messages": user_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


def anthropic_messages(base_url: str, api_key: str, payload: dict, timeout: int) -> dict:
    url = base_url.rstrip("/") + "/messages"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body[:2000]}") from e


def extract_response_text(api: str, response: dict) -> str:
    if api == "openai-completions":
        return response.get("choices", [{}])[0].get("message", {}).get("content", "")
    if api == "anthropic-messages":
        parts = []
        for item in response.get("content", []) or []:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "".join(parts)
    return ""

def build_log_record(
    *,
    project_root: str,
    chapter_id: str,
    model: str,
    api: str,
    base_url: str,
    temperature: float,
    max_tokens: int,
    prompt_profile: str,
    included: list[IncludedFile],
    execute: bool,
    status: str,
    elapsed_seconds: float | None = None,
    output_chars: int | None = None,
    usage: dict | None = None,
    error: str | None = None,
    request_preview: str = "",
    manifest_path: str = "",
    output_path: str = "",
) -> dict:
    """Build a single API call log record (full detail)."""
    input_chars = sum(item.chars for item in included)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": project_root,
        "chapterId": chapter_id,
        "model": model,
        "api": api,
        "baseUrl": base_url.rstrip("/") if base_url else "",
        "status": status,
        "temperature": temperature,
        "maxTokens": max_tokens,
        "promptProfile": prompt_profile,
        "inputFiles": [{"path": item.rel, "chars": item.chars} for item in included],
        "inputChars": input_chars,
    }
    if elapsed_seconds is not None:
        record["elapsedSeconds"] = elapsed_seconds
    if output_chars is not None:
        record["outputChars"] = output_chars
    if usage:
        record["usage"] = usage
    if error:
        record["error"] = str(error)[:2000]
    if request_preview:
        record["requestPreview"] = request_preview
    if manifest_path:
        record["manifestPath"] = manifest_path
    if output_path:
        record["outputPath"] = output_path
    return record


def trim_log_record(record: dict) -> dict:
    """Trim a full record down to metadata-only (drop requestPreview/manifestPath/outputPath/inputFiles/error/details)."""
    keep_keys = {
        "timestamp", "chapterId", "model", "api", "baseUrl",
        "status", "temperature", "maxTokens", "promptProfile",
        "inputChars", "outputChars", "elapsedSeconds", "usage",
    }
    return {k: v for k, v in record.items() if k in keep_keys}


# write_direct_api_config removed — model config is now global only.
# present_error_recovery removed — error recovery is now delegated to system model.


def _auto_fallback_to_system(direct_cfg: dict | None) -> tuple[bool, str]:
    """Auto-switch workMode to 'system' on API failure.
    Returns (switched, previous_mode)."""
    if not GLOBAL_CONFIG_PATH.exists():
        return False, "config_missing"
    try:
        full_cfg = json.loads(GLOBAL_CONFIG_PATH.read_text(encoding="utf-8"))
        old_mode = full_cfg.get("workMode", "direct")
        if old_mode == "system":
            return False, "already_system"
        full_cfg["workMode"] = "system"
        GLOBAL_CONFIG_PATH.write_text(json.dumps(full_cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return True, old_mode
    except Exception as write_err:
        return False, f"write_error: {write_err}"


def update_api_call_log(record: dict) -> None:
    """Append a record to the API call log, keeping last MAX_LOG_ENTRIES.
    The most recent FULL_DETAIL_KEEP records keep full detail; older ones are trimmed.
    Log file lives under the Novel Studio skill directory, not the novel project."""
    log_dir = skill_root() / ".novel-studio" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / API_CALL_LOG_FILE

    entries: list[dict] = []
    if log_path.exists():
        try:
            entries = json.loads(log_path.read_text(encoding="utf-8"))
            if not isinstance(entries, list):
                entries = []
        except Exception:
            entries = []

    # Append new record (always full detail)
    entries.append(record)

    # Enforce max entries: drop oldest
    while len(entries) > MAX_LOG_ENTRIES:
        entries.pop(0)

    # Trim detail: keep last FULL_DETAIL_KEEP as full, trim the rest
    trim_cutoff = max(0, len(entries) - FULL_DETAIL_KEEP)
    for i in range(trim_cutoff):
        entries[i] = trim_log_record(entries[i])

    log_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("chapter_id")
    ap.add_argument("--input-pack", default=None, help="input pack path; default .novel-studio/logs/<chapter>-input-pack.md")
    ap.add_argument("--base-url", default=os.environ.get(DEFAULT_BASE_URL_ENV, ""))
    ap.add_argument("--model", default=os.environ.get(DEFAULT_MODEL_ENV, ""))
    ap.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=6000)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--max-chars-per-file", type=int, default=30000)
    ap.add_argument("--max-total-chars", type=int, default=120000)
    ap.add_argument("--prompt-profile", default="draft", choices=["draft", "rewrite", "humanize", "review"])
    ap.add_argument("--instruction", default="")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="write request preview only; default")
    mode.add_argument("--execute", action="store_true", help="perform real API call")
    args = ap.parse_args()

    root = Path(args.project_dir).expanduser().resolve()
    chapter_id = args.chapter_id
    input_pack = Path(args.input_pack).expanduser().resolve() if args.input_pack else root / ".novel-studio" / "logs" / f"{chapter_id}-input-pack.md"
    if not input_pack.exists():
        print(f"input pack not found: {input_pack}", file=sys.stderr)
        print(f"hint: run scripts/workflow_runner.py {root} {chapter_id} chapter-full first", file=sys.stderr)
        return 1

    base_url = args.base_url
    model = args.model
    api_key_env = args.api_key_env
    # Model config is now GLOBAL only — all projects share one config.
    direct_cfg, cfg_source = read_global_direct_api()
    has_project_config = direct_cfg is not None
    system_model = None
    if has_project_config:
        if not direct_cfg.get("systemModel"):
            print(f"direct API config is missing systemModel: {cfg_source}", file=sys.stderr)
            print(f"hint: run scripts/ns_model_config.py global set", file=sys.stderr)
            return 2
        if direct_cfg.get("api") not in SUPPORTED_API:
            print(f"configured model is not direct-API compatible: {direct_cfg.get('systemModel')} (api={direct_cfg.get('api')})", file=sys.stderr)
            print(f"hint: run scripts/ns_model_config.py global set", file=sys.stderr)
            return 2
        system_model = {
            "provider": (direct_cfg.get("modelConfig") or {}).get("provider", ""),
            "model": direct_cfg.get("model", ""),
            "modelFull": direct_cfg.get("systemModel", ""),
            "baseUrl": direct_cfg.get("baseUrl", ""),
            "api": direct_cfg.get("api", ""),
            "modelConfig": direct_cfg.get("modelConfig"),
            "providerConfig": direct_cfg.get("providerConfig"),
            "source": direct_cfg.get("source"),
        }
        model = model or direct_cfg.get("model", "")
        base_url = base_url or direct_cfg.get("baseUrl", "")
        api_key_env = args.api_key_env if args.api_key_env != DEFAULT_API_KEY_ENV else direct_cfg.get("apiKeyEnv", api_key_env)
        if args.temperature == 0.7 and direct_cfg.get("temperature") is not None:
            args.temperature = float(direct_cfg.get("temperature"))
        if args.max_tokens == 6000 and direct_cfg.get("maxTokens") is not None:
            args.max_tokens = int(direct_cfg.get("maxTokens"))
    if not model or not base_url:
        print("direct API model is not configured for this project.", file=sys.stderr)
        print(f"hint: run scripts/ns_model_config.py global set", file=sys.stderr)
        print("or pass both --model and --base-url explicitly.", file=sys.stderr)
        if has_project_config:
            print(f"config exists but is incomplete: {cfg_source}", file=sys.stderr)
        return 2

    api_key = (direct_cfg or {}).get("apiKey") or os.environ.get(api_key_env, "")
    execute = bool(args.execute)

    paths = extract_pack_paths(root, input_pack)
    included = load_included_files(root, paths, args.max_chars_per_file, args.max_total_chars)
    state_path = root / ".novel-studio" / "state.json"
    project_name = root.name
    if state_path.exists():
        try:
            project_name = json.loads(read_text(state_path)).get("project") or project_name
        except Exception:
            pass

    messages = build_messages(chapter_id, project_name, included, args.prompt_profile, args.instruction)
    resolved_model_config = system_model.get("modelConfig") if 'system_model' in locals() and system_model else None
    resolved_provider_config = system_model.get("providerConfig") if 'system_model' in locals() and system_model else None
    api = (resolved_model_config or {}).get("api") or (system_model.get("api") if 'system_model' in locals() and system_model else "openai-completions")

    # --- Work mode check ---
    full_cfg, _ = _read_full_global_config()
    work_mode = "direct"
    if full_cfg and full_cfg.get("workMode") in ("system", "direct"):
        work_mode = full_cfg["workMode"]
    if args.execute and work_mode == "system":
        print("=" * 55, file=sys.stderr)
        print("⚠️  当前工作模式为「系统模型」，直连 API 不可用。", file=sys.stderr)
        print("   只有创作/写作/修稿任务在「直连模式」下才走 API。", file=sys.stderr)
        print("   切换: python3 scripts/ns_model_config.py workmode set direct", file=sys.stderr)
        print("=" * 55, file=sys.stderr)
        return 4

    if api == "openai-completions":
        payload = {
            "model": model,
            "messages": messages,
            "temperature": args.temperature,
            "max_tokens": args.max_tokens,
        }
    elif api == "anthropic-messages":
        payload = anthropic_messages_payload(model, messages, args.temperature, args.max_tokens)
    else:
        print(f"unsupported direct API protocol: {api}", file=sys.stderr)
        return 2

    out_dir = root / ".novel-studio" / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_stamp()
    base = out_dir / f"{chapter_id}-direct-api-{stamp}"
    preview_path = base.with_suffix(".request.json")
    manifest_path = base.with_suffix(".manifest.json")
    output_path = base.with_suffix(".md")

    preview_payload = dict(payload)
    preview_path.write_text(json.dumps(preview_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = {
        "projectRoot": str(root),
        "project": project_name,
        "chapterId": chapter_id,
        "inputPack": str(input_pack.relative_to(root)),
        "includedFiles": [{"path": item.rel, "chars": item.chars} for item in included],
        "promptProfile": args.prompt_profile,
        "model": payload["model"],
        "api": api,
        "configuredSystemModel": direct_cfg.get("systemModel") if isinstance(direct_cfg, dict) else None,
        "configuredModel": direct_cfg.get("model") if isinstance(direct_cfg, dict) else None,
        "resolvedModelConfig": redact_secrets(resolved_model_config),
        "resolvedProviderConfig": redact_secrets(resolved_provider_config),
        "baseUrl": base_url.rstrip("/") if base_url else "BASE_URL_NOT_SET",
        "apiKeyEnv": api_key_env,
        "execute": execute,
        "temperature": args.temperature,
        "maxTokens": args.max_tokens,
        "requestPreview": str(preview_path.relative_to(root)),
        "output": str(output_path.relative_to(root)),
        "createdAtUtc": datetime.now(timezone.utc).isoformat(),
    }

    if not execute:
        output_path.write_text("# Direct API dry-run\n\nNo API request was sent. Review the request preview and manifest first.\n", encoding="utf-8")
        manifest["status"] = "dry-run"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"dry-run request written: {preview_path}")
        print(f"manifest written: {manifest_path}")
        print(f"included files: {len(included)}")
        log_record = build_log_record(
            project_root=str(root),
            chapter_id=chapter_id, model=model, api=api, base_url=base_url,
            temperature=args.temperature, max_tokens=args.max_tokens,
            prompt_profile=args.prompt_profile, included=included,
            execute=False, status="dry-run",
            request_preview=str(preview_path.relative_to(root)),
            manifest_path=str(manifest_path.relative_to(root)),
        )
        update_api_call_log(log_record)
        return 0

    if not base_url:
        print(f"missing base url; set --base-url or {DEFAULT_BASE_URL_ENV}", file=sys.stderr)
        return 2
    if not model:
        print(f"missing model; set --model or {DEFAULT_MODEL_ENV}", file=sys.stderr)
        return 2
    if not api_key:
        print(f"missing api key env: {api_key_env}", file=sys.stderr)
        return 2

    # --- Execute ---
    out_dir = root / ".novel-studio" / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_stamp()
    base = out_dir / f"{chapter_id}-direct-api-{stamp}"
    preview_path = base.with_suffix(".request.json")
    manifest_path = base.with_suffix(".manifest.json")
    output_path = base.with_suffix(".md")

    preview_payload = dict(payload)
    preview_path.write_text(json.dumps(preview_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = {
        "projectRoot": str(root),
        "project": project_name,
        "chapterId": chapter_id,
        "inputPack": str(input_pack.relative_to(root)),
        "includedFiles": [{"path": item.rel, "chars": item.chars} for item in included],
        "promptProfile": args.prompt_profile,
        "model": model,
        "api": api,
        "configuredSystemModel": direct_cfg.get("systemModel") if isinstance(direct_cfg, dict) else None,
        "configuredModel": direct_cfg.get("model") if isinstance(direct_cfg, dict) else None,
        "resolvedModelConfig": redact_secrets(resolved_model_config),
        "resolvedProviderConfig": redact_secrets(resolved_provider_config),
        "baseUrl": base_url.rstrip("/") if base_url else "BASE_URL_NOT_SET",
        "apiKeyEnv": api_key_env,
        "execute": True,
        "temperature": args.temperature,
        "maxTokens": args.max_tokens,
        "requestPreview": str(preview_path.relative_to(root)),
        "output": str(output_path.relative_to(root)),
        "createdAtUtc": datetime.now(timezone.utc).isoformat(),
    }

    started = time.time()
    try:
        if api == "openai-completions":
            response = chat_completions(base_url, api_key, payload, args.timeout)
        elif api == "anthropic-messages":
            response = anthropic_messages(base_url, api_key, payload, args.timeout)
        else:
            raise RuntimeError(f"unsupported direct API protocol: {api}")
        content = extract_response_text(api, response)
        if not content:
            content = json.dumps(response, ensure_ascii=False, indent=2)
        output_path.write_text(content, encoding="utf-8")
        elapsed = round(time.time() - started, 3)
        manifest["status"] = "ok"
        manifest["elapsedSeconds"] = elapsed
        usage = response.get("usage")
        if usage:
            manifest["usage"] = usage
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"output written: {output_path}")
        print(f"manifest written: {manifest_path}")
        log_record = build_log_record(
            project_root=str(root),
            chapter_id=chapter_id, model=model, api=api, base_url=base_url,
            temperature=args.temperature, max_tokens=args.max_tokens,
            prompt_profile=args.prompt_profile, included=included,
            execute=True, status="ok",
            elapsed_seconds=elapsed,
            output_chars=len(content),
            usage=usage,
            request_preview=str(preview_path.relative_to(root)),
            manifest_path=str(manifest_path.relative_to(root)),
            output_path=str(output_path.relative_to(root)),
        )
        update_api_call_log(log_record)
        return 0

    except Exception as e:
        elapsed = round(time.time() - started, 3)
        manifest["status"] = "error"
        manifest["error"] = str(e)
        manifest["elapsedSeconds"] = elapsed
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        log_record = build_log_record(
            project_root=str(root),
            chapter_id=chapter_id, model=model, api=api, base_url=base_url,
            temperature=args.temperature, max_tokens=args.max_tokens,
            prompt_profile=args.prompt_profile, included=included,
            execute=True, status="error",
            elapsed_seconds=elapsed,
            error=str(e),
            request_preview=str(preview_path.relative_to(root)),
            manifest_path=str(manifest_path.relative_to(root)),
        )
        update_api_call_log(log_record)

        # Diagnose error and suggest next steps
        err_str = str(e).lower()
        suggestions: list[str] = []
        if "401" in err_str or "403" in err_str or "unauthorized" in err_str or "invalid api key" in err_str:
            suggestions.append("API Key 可能无效或过期")
        if "404" in err_str or "not found" in err_str:
            suggestions.append("模型名称或 Base URL 可能不正确")
        if "429" in err_str or "rate" in err_str or "quota" in err_str:
            suggestions.append("触发限流，建议等待后重试或切换模型")
        if "schema" in err_str or "tool" in err_str or "payload" in err_str:
            suggestions.append("请求格式被 provider 拒绝，可能是 API 协议不匹配")
        if "timeout" in err_str or "timed out" in err_str:
            suggestions.append("请求超时，可尝试更轻量的模型或减少输入量")
        if not suggestions:
            suggestions.append("可能是临时网络问题，或模型暂时不可用")

        # Auto-fallback: switch workMode to system model
        fallback_switched, fallback_prev = _auto_fallback_to_system(direct_cfg)

        # Record session failure via ns_session.py
        _ns_session_path = Path(__file__).resolve().parent / "ns_session.py"
        if _ns_session_path.exists():
            try:
                subprocess.run(
                    [sys.executable, str(_ns_session_path), "fail", str(root),
                     "--error", str(e)[:500],
                     "--suggestions", "; ".join(suggestions)],
                    capture_output=True, timeout=10,
                )
            except Exception:
                pass  # session recording is best-effort

        # Output structured error for system model to handle recovery
        error_output = {
            "ns_direct_api_error": {
                "model": model,
                "api": api,
                "baseUrl": base_url.rstrip("/") if base_url else "",
                "error": str(e)[:500],
                "suggestions": suggestions,
                "chapterId": chapter_id,
                "project": project_name,
                "manifestPath": str(manifest_path.relative_to(root)),
                "configMode": (direct_cfg or {}).get("configMode", ""),
                "systemModel": (direct_cfg or {}).get("systemModel", ""),
                "fallbackToSystem": fallback_switched,
                "previousWorkMode": fallback_prev,
            }
        }

        print("\n" + "=" * 60, file=sys.stderr)
        print("❌ Direct API 调用失败", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(f"  模型:     {model}", file=sys.stderr)
        print(f"  API:      {api}", file=sys.stderr)
        print(f"  Base URL: {base_url}", file=sys.stderr)
        print(f"  错误:     {str(e)[:300]}", file=sys.stderr)
        for s in suggestions:
            print(f"  💡 {s}", file=sys.stderr)
        if fallback_switched:
            print(file=sys.stderr)
            print("🔄 已自动切换工作模式: 直连模式 → 系统模型", file=sys.stderr)
            print("   系统模型已接管，将继续处理你的请求。", file=sys.stderr)
            print("   稍后可用「配置模型」重新设置直连 API。", file=sys.stderr)
        print(file=sys.stderr)
        print("═══ NS_DIRECT_API_ERROR " + json.dumps(error_output, ensure_ascii=False), file=sys.stderr)
        print(file=sys.stderr)

        return 3


if __name__ == "__main__":
    raise SystemExit(main())
