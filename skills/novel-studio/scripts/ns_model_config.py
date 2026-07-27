#!/usr/bin/env python3
"""
ns_model_config.py

Discover OpenClaw system model config and initialize/select Novel Studio direct
API model settings for a project.

This script stores a verified direct API model snapshot (including apiKey) in
project config plus the system model name used for future sync. Display output redacts secrets.

Usage:
  python3 scripts/ns_model_config.py list [--json]
  python3 scripts/ns_model_config.py init <project-dir> [--select <provider/model|alias|number>] [--non-interactive]
  python3 scripts/ns_model_config.py global sync
  python3 scripts/ns_model_config.py sync <project-dir>    # deprecated → use global sync
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import os
import sys

DEFAULT_CONFIG_PATHS = [
    Path("/root/.openclaw/openclaw.json"),
    Path("/root/.openclaw/agents/main/agent/models.json"),
]
SUPPORTED_API = {"openai-completions", "anthropic-messages"}
KEY_ENV_PREFIX = "NOVEL_STUDIO_API_KEY_"
GLOBAL_CONFIG_DIR = Path(__file__).resolve().parent.parent / ".novel-studio"
GLOBAL_CONFIG_PATH = GLOBAL_CONFIG_DIR / "global-config.json"


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


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
        if k not in {"models"}
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


def aliases_from_config(data: dict) -> dict:
    out = {}
    agents = data.get("agents") if isinstance(data.get("agents"), dict) else {}
    defaults = agents.get("defaults") if isinstance(agents.get("defaults"), dict) else {}
    models = defaults.get("models") if isinstance(defaults.get("models"), dict) else {}
    for full, meta in models.items():
        if isinstance(meta, dict) and meta.get("alias"):
            out[meta["alias"]] = full
    return out


def discover() -> list[dict]:
    aliases = {}
    configs = [(cfg, load_json(cfg)) for cfg in DEFAULT_CONFIG_PATHS]
    for _, data in configs:
        aliases.update(aliases_from_config(data))
    rows = []
    seen = set()
    for cfg, data in configs:
        providers = providers_from_config(data)
        for provider_id, provider in providers.items():
            if not isinstance(provider, dict):
                continue
            base_url = provider.get("baseUrl") or provider.get("baseURL") or provider.get("base_url") or ""
            provider_api = provider.get("api") or ""
            models = provider.get("models") or []
            for m in models:
                if not isinstance(m, dict):
                    continue
                model_id = m.get("id")
                if not model_id:
                    continue
                effective_config = inherited_model_config(provider_id, provider, m)
                api = effective_config.get("api", "")
                full = f"{provider_id}/{model_id}"
                key = full
                if key in seen:
                    continue
                seen.add(key)
                supported = api in SUPPORTED_API and "image" not in str(model_id).lower()
                rows.append({
                    "full": full,
                    "provider": provider_id,
                    "model": model_id,
                    "name": m.get("name") or model_id,
                    "alias": next((a for a, target in aliases.items() if target == full), ""),
                    "baseUrl": effective_config.get("baseUrl", ""),
                    "api": effective_config.get("api", ""),
                    "supportedDirectApi": supported,
                    "contextWindow": effective_config.get("contextWindow"),
                    "maxTokens": effective_config.get("maxTokens"),
                    "modelConfig": effective_config,
                    "providerConfig": {k: v for k, v in provider.items() if k not in {"models"}},
                    "source": str(cfg),
                })
    # Prefer supported OpenAI-compatible models first, then stable display order.
    rows.sort(key=lambda r: (not r["supportedDirectApi"], r["provider"], r["model"], r["source"]))
    return rows


def print_table(rows: list[dict]) -> None:
    for i, r in enumerate(rows, start=1):
        support = "direct" if r["supportedDirectApi"] else f"api={r['api'] or 'unknown'}"
        alias = f" alias={r['alias']}" if r.get("alias") else ""
        print(f"{i}. {r['full']} ({r['name']}){alias} — {support} — {r['baseUrl'] or 'no baseUrl'}")


def resolve_selection(rows: list[dict], select: str | None) -> dict | None:
    supported = [r for r in rows if r["supportedDirectApi"]]
    if not rows:
        return None
    if not select:
        return supported[0] if supported else rows[0]
    s = select.strip()
    s_lower = s.lower()
    if s.isdigit():
        idx = int(s) - 1
        if 0 <= idx < len(rows):
            return rows[idx]
        return None
    for r in rows:
        candidates = {r["full"], r["model"], r.get("alias", "")}
        if s in candidates or s_lower in {c.lower() for c in candidates if c}:
            return r
    return None


def interactive_select(rows: list[dict]) -> dict | None:
    print_table(rows)
    print("\nChoose a model number/full id/alias. Empty = first direct-compatible model.")
    try:
        choice = input("> ").strip()
    except EOFError:
        choice = ""
    return resolve_selection(rows, choice or None)


def env_name_for(provider: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in provider.upper())
    return KEY_ENV_PREFIX + safe


# project_config_path removed — model config is now global only.


# ensure_config_gitignore removed — model config is now global only.


def ensure_supported(row: dict) -> tuple[bool, str]:
    if not row:
        return False, "model not found"
    if not row.get("supportedDirectApi"):
        return False, f"model api is not supported: {row.get('api')}"
    if not row.get("baseUrl"):
        return False, "model has no baseUrl"
    return True, ""


def build_direct_api_config(row: dict, key_env: str | None, previous: dict | None = None,
                           config_mode: str = "imported") -> dict:
    previous = previous or {}
    provider_cfg = row.get("providerConfig") or {}
    api_key = provider_cfg.get("apiKey") or previous.get("apiKey") or ""
    data = {
        "systemModel": row["full"],
        "model": row["model"],
        "api": row.get("api", ""),
        "baseUrl": row.get("baseUrl", ""),
        "apiKey": api_key,
        "apiKeyEnv": key_env or previous.get("apiKeyEnv") or env_name_for(row["provider"]),
        "temperature": previous.get("temperature", 0.7),
        "maxTokens": previous.get("maxTokens") or row.get("maxTokens"),
        "modelConfig": row.get("modelConfig"),
        "providerConfig": provider_cfg,
        "source": row.get("source"),
        "configMode": config_mode,
    }
    return data


# write_project_config removed — model config is now global only.


def redact_secrets(value):
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k.lower() == "apikey":
                out[k] = "***" if v else ""
            else:
                out[k] = redact_secrets(v)
        return out
    if isinstance(value, list):
        return [redact_secrets(v) for v in value]
    return value


# read_project_config removed — model config is now global only.


# validate_project removed — model config is now global only. Use global show instead.


# sync_project removed — model config is now global only.


# show_project removed — model config is now global only. Use global show instead.


def read_global_config() -> tuple[dict | None, Path]:
    """Read the Novel Studio global config (directApi + workMode)."""
    if GLOBAL_CONFIG_PATH.exists():
        try:
            config = json.loads(GLOBAL_CONFIG_PATH.read_text(encoding="utf-8"))
            return config, GLOBAL_CONFIG_PATH
        except Exception:
            pass
    return None, GLOBAL_CONFIG_PATH


def read_global_direct_api() -> tuple[dict | None, Path]:
    """Read the Novel Studio global direct API config only."""
    config, path = read_global_config()
    if config and isinstance(config.get("directApi"), dict):
        return config["directApi"], path
    return None, path


def read_global_work_mode() -> str:
    """Read the current work mode: 'system' or 'direct'. Default 'direct'."""
    config, _ = read_global_config()
    if config and config.get("workMode") in ("system", "direct"):
        return config["workMode"]
    return "direct"


def write_global_config(config: dict) -> None:
    GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    GLOBAL_CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_model_connectivity(row: dict, timeout: int = 15) -> tuple[bool, str]:
    """Attempt a minimal API call to verify the selected model is reachable.
    Returns (ok, message)."""
    from urllib import request, error
    api = row.get("api", "")
    base_url = row.get("baseUrl", "")
    model_id = row.get("model", "")
    provider_cfg = row.get("providerConfig") or {}
    api_key = provider_cfg.get("apiKey") or ""

    if not api_key:
        return False, "无法获取 API Key（providerConfig 中缺少 apiKey）"
    if not base_url:
        return False, "缺少 baseUrl"

    try:
        if api == "openai-completions":
            url = base_url.rstrip("/") + "/chat/completions"
            payload = json.dumps({
                "model": model_id,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
            }, ensure_ascii=False).encode("utf-8")
            req = request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }, method="POST")
        elif api == "anthropic-messages":
            url = base_url.rstrip("/") + "/messages"
            payload = json.dumps({
                "model": model_id,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
            }, ensure_ascii=False).encode("utf-8")
            req = request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            }, method="POST")
        else:
            return False, f"不支持的 API 协议: {api}"

        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return True, f"连接成功 (HTTP {resp.status})"
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        return False, f"HTTP {e.code}: {body}"
    except Exception as e:
        return False, f"连接失败: {str(e)[:200]}"


def _prompt_config_mode(row: dict, non_interactive: bool, custom_mode: bool) -> str:
    """Ask user: import from system or manual config.
    Returns 'import' or 'custom'."""
    if custom_mode:
        return "custom"
    if non_interactive:
        return "import"
    print()
    print(f"已选择: {row['full']} ({row.get('name', '')})")
    print(f"  baseUrl: {row.get('baseUrl', 'N/A')}")
    print(f"  api:     {row.get('api', 'N/A')}")
    print()
    print("配置方式:")
    print("  1. 系统导入 — 直接从 OpenClaw 系统配置导入（baseUrl/apiKey 等自动填入）")
    print("  2. 手动配置 — 自行输入 baseUrl、apiKey、API 格式、上下文长度等")
    print()
    try:
        choice = input("选择 [1/2] (默认 1): ").strip()
    except EOFError:
        choice = ""
    if choice == "2":
        return "custom"
    return "import"


def _interactive_custom_config(row: dict) -> dict:
    """Prompt user for manual model config fields."""
    print()
    print("═══ 手动配置直连 API 模型 ═══")
    print()

    # baseUrl
    default_url = row.get("baseUrl", "")
    prompt = f"baseUrl [{default_url}]: "
    try:
        base_url = input(prompt).strip()
    except EOFError:
        base_url = ""
    if not base_url:
        base_url = default_url

    # API protocol
    default_api = row.get("api", "openai-completions")
    print()
    print("API 协议:")
    print("  1. openai-completions  → POST /chat/completions")
    print("  2. anthropic-messages  → POST /messages")
    try:
        api_choice = input(f"选择 [1/2] (默认 {'1' if default_api == 'openai-completions' else '2'}): ").strip()
    except EOFError:
        api_choice = ""
    if api_choice == "2":
        api = "anthropic-messages"
    elif api_choice == "1":
        api = "openai-completions"
    else:
        api = default_api

    # apiKey
    default_key = (row.get("providerConfig") or {}).get("apiKey", "")
    print()
    try:
        key_input = input(f"apiKey [{default_key[:8]}... 回车沿用]: ").strip()
    except EOFError:
        key_input = ""
    api_key = key_input if key_input else default_key

    # model ID
    default_model = row.get("model", "")
    try:
        model_input = input(f"model ID [{default_model}]: ").strip()
    except EOFError:
        model_input = ""
    model_id = model_input if model_input else default_model

    # contextWindow
    default_ctx = row.get("contextWindow")
    ctx_prompt = f"上下文窗口 [{default_ctx}]: " if default_ctx else "上下文窗口 (留空跳过): "
    try:
        ctx_input = input(ctx_prompt).strip()
    except EOFError:
        ctx_input = ""
    context_window = int(ctx_input) if ctx_input else default_ctx

    # maxTokens
    default_max = row.get("maxTokens")
    max_prompt = f"maxTokens [{default_max}]: " if default_max else "maxTokens (留空跳过): "
    try:
        max_input = input(max_prompt).strip()
    except EOFError:
        max_input = ""
    max_tokens = int(max_input) if max_input else default_max

    # temperature
    try:
        temp_input = input("temperature [0.7]: ").strip()
    except EOFError:
        temp_input = ""
    temperature = float(temp_input) if temp_input else 0.7

    print()

    provider = row.get("provider", "custom")
    full_id = f"{provider}/{model_id}"

    return {
        "full": full_id,
        "provider": provider,
        "model": model_id,
        "name": model_id,
        "alias": "",
        "baseUrl": base_url,
        "api": api,
        "supportedDirectApi": True,
        "contextWindow": context_window,
        "maxTokens": max_tokens,
        "modelConfig": {
            "provider": provider,
            "id": model_id,
            "name": model_id,
            "baseUrl": base_url,
            "api": api,
            "contextWindow": context_window,
            "maxTokens": max_tokens,
        },
        "providerConfig": {
            "apiKey": api_key,
            "baseUrl": base_url,
            "api": api,
        },
        "source": "manual",
        "_custom_temperature": temperature,
    }


def set_global(select: str | None, non_interactive: bool, api_key_env: str | None,
               skip_validate: bool = False, custom: bool = False) -> int:
    rows = discover()
    if select or non_interactive:
        row = resolve_selection(rows, select)
    else:
        row = interactive_select(rows)
    if not row:
        print("no model selected", file=sys.stderr)
        return 1

    # --- Choose config mode: import vs custom ---
    config_mode = _prompt_config_mode(row, non_interactive, custom)

    if config_mode == "custom":
        row = _interactive_custom_config(row)
        custom_temp = row.pop("_custom_temperature", 0.7)

    # Validate support (only for imported models; custom ones are assumed supported)
    if config_mode == "import":
        ok, reason = ensure_supported(row)
        if not ok:
            print(f"selected model is not usable for direct API: {row.get('full') if row else ''}; {reason}", file=sys.stderr)
            return 2

    GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    existing = {}
    if GLOBAL_CONFIG_PATH.exists():
        try:
            existing = json.loads(GLOBAL_CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            existing = {}

    # --- Validation step ---
    if not skip_validate:
        if config_mode == "custom":
            print(f"🔍 正在验证手动配置连通性 ...", file=sys.stderr)
        else:
            print(f"🔍 正在验证模型连通性: {row['full']} ...", file=sys.stderr)
        print(f"   baseUrl: {row.get('baseUrl', 'N/A')}", file=sys.stderr)
        valid, vmsg = validate_model_connectivity(row)
        if not valid:
            print(f"❌ 验证失败: {vmsg}", file=sys.stderr)
            print(f"   配置已放弃，未保存任何更改。", file=sys.stderr)
            print(f"   提示: 可换一个模型重试，或用 --skip-validate 跳过验证。", file=sys.stderr)
            return 2
        print(f"✅ 验证通过: {vmsg}", file=sys.stderr)
    else:
        print(f"⚠️  已跳过连通性验证 (--skip-validate)", file=sys.stderr)

    previous = existing.get("directApi")
    if config_mode == "custom":
        existing["directApi"] = build_direct_api_config(row, api_key_env, previous=previous, config_mode="manual")
        if custom_temp is not None:
            existing["directApi"]["temperature"] = custom_temp
    else:
        existing["directApi"] = build_direct_api_config(row, api_key_env, previous=previous, config_mode="imported")

    write_global_config(existing)
    mode_label = "手动配置" if config_mode == "custom" else "系统导入"
    print(f"wrote global direct API config ({mode_label}): {GLOBAL_CONFIG_PATH}")
    print(f"selected: {row['full']}")
    print(f"api key env: {api_key_env or env_name_for(row['provider'])}")
    return 0


def show_global() -> int:
    cfg, path = read_global_direct_api()
    full_cfg, _ = read_global_config()
    if not cfg:
        print(f"global direct API config not found: {GLOBAL_CONFIG_PATH}")
        return 1
    result = {"configPath": str(path), "directApi": redact_secrets(cfg)}
    if full_cfg:
        result["workMode"] = full_cfg.get("workMode", "direct")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def remove_global() -> int:
    if GLOBAL_CONFIG_PATH.exists():
        GLOBAL_CONFIG_PATH.unlink()
        print(f"removed: {GLOBAL_CONFIG_PATH}")
    else:
        print(f"no global config to remove: {GLOBAL_CONFIG_PATH}")
    return 0


def workmode_show() -> int:
    mode = read_global_work_mode()
    label = "🔵 直连模式 (direct)" if mode == "direct" else "🟢 系统模型 (system)"
    print(f"当前工作模式: {label}")
    print(f"  direct = 创作/写作/修稿走直连 API")
    print(f"  system = 所有任务走 OpenClaw 系统模型")
    return 0


def workmode_set(mode: str) -> int:
    if mode not in ("system", "direct"):
        print(f"invalid work mode: {mode}. Use 'system' or 'direct'.", file=sys.stderr)
        return 1
    config, _ = read_global_config()
    config = config or {}
    config["workMode"] = mode
    write_global_config(config)
    label = "🔵 直连模式 (direct)" if mode == "direct" else "🟢 系统模型 (system)"
    print(f"工作模式已切换为: {label}")
    return 0


def sync_global() -> int:
    """Sync the global direct API config with current system model config.

    Only allowed when configMode == 'imported'. Manual configs are rejected.
    """
    full_cfg, _ = read_global_config()
    if not full_cfg or not isinstance(full_cfg.get("directApi"), dict):
        print("❌ 全局 direct API 配置不存在，请先运行 `global set` 配置模型。", file=sys.stderr)
        return 1

    direct_api = full_cfg["directApi"]
    config_mode = direct_api.get("configMode", "")

    if config_mode != "imported":
        reason = "手动配置" if config_mode == "manual" else f"未知来源 ({config_mode or '缺失'})"
        print(f"❌ 拒绝同步: 当前配置为「{reason}」，仅系统导入的配置支持同步。", file=sys.stderr)
        print(f"   提示: 用 `global set` 重新选择模型并选「系统导入」来建立可同步的配置。", file=sys.stderr)
        return 2

    system_model = direct_api.get("systemModel", "")
    if not system_model:
        print("❌ 当前配置缺少 systemModel 字段，无法同步。", file=sys.stderr)
        return 1

    # Re-discover system models
    rows = discover()
    if not rows:
        print("❌ 无法获取系统模型列表。", file=sys.stderr)
        return 1

    # Find matching model by full name
    match = None
    for r in rows:
        if r["full"] == system_model:
            match = r
            break

    if not match:
        print(f"❌ 系统模型列表中找不到「{system_model}」。", file=sys.stderr)
        print(f"   该模型可能已被移除或重命名。请用 `global set` 重新选择。", file=sys.stderr)
        return 2

    # Check support
    ok, reason = ensure_supported(match)
    if not ok:
        print(f"❌ 「{system_model}」当前系统配置不支持直连 API: {reason}", file=sys.stderr)
        print(f"   请用 `global set` 选择其他可用模型。", file=sys.stderr)
        return 2

    # Sync: rebuild config from fresh system data, preserve apiKey/temperature from old config
    previous = direct_api
    full_cfg["directApi"] = build_direct_api_config(match, previous.get("apiKeyEnv"), previous=previous, config_mode="imported")
    write_global_config(full_cfg)

    print(f"✅ 同步成功: {system_model}")
    print(f"   baseUrl: {match.get('baseUrl', 'N/A')}")
    print(f"   api:     {match.get('api', 'N/A')}")
    print(f"   configMode: imported")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_list = sub.add_parser("list")
    p_list.add_argument("--json", action="store_true")
    # --- deprecated project-level commands (kept for compat messages) ---
    p_init = sub.add_parser("init")
    p_init.add_argument("project_dir")
    p_init.add_argument("--select", default=None)
    p_init.add_argument("--non-interactive", action="store_true")
    p_init.add_argument("--api-key-env", default=None)
    p_show = sub.add_parser("show")
    p_show.add_argument("project_dir")
    p_validate = sub.add_parser("validate")
    p_validate.add_argument("project_dir")
    p_sync = sub.add_parser("sync")
    p_sync.add_argument("project_dir")
    # --- global commands ---
    p_global = sub.add_parser("global")
    p_global_sub = p_global.add_subparsers(dest="global_cmd")
    p_global_set = p_global_sub.add_parser("set")
    p_global_set.add_argument("--select", default=None)
    p_global_set.add_argument("--non-interactive", action="store_true")
    p_global_set.add_argument("--api-key-env", default=None)
    p_global_set.add_argument("--skip-validate", action="store_true",
                              help="skip connectivity validation after selection")
    p_global_set.add_argument("--custom", action="store_true",
                              help="manual config mode: enter baseUrl/apiKey/etc. instead of importing from system")
    p_global_sub.add_parser("show")
    p_global_sub.add_parser("remove")
    p_global_sub.add_parser("sync")
    # --- workmode commands ---
    p_workmode = sub.add_parser("workmode")
    p_workmode_sub = p_workmode.add_subparsers(dest="workmode_cmd")
    p_workmode_sub.add_parser("show")
    p_workmode_set = p_workmode_sub.add_parser("set")
    p_workmode_set.add_argument("mode", choices=["system", "direct"],
                                help="'system' = all tasks use OpenClaw system model; 'direct' = creative tasks use direct API")
    args = ap.parse_args()

    if args.cmd == "global":
        if args.global_cmd == "set":
            return set_global(args.select, args.non_interactive, args.api_key_env,
                            skip_validate=args.skip_validate, custom=args.custom)
        if args.global_cmd == "show":
            return show_global()
        if args.global_cmd == "remove":
            return remove_global()
        if args.global_cmd == "sync":
            return sync_global()
        print("usage: ns_model_config.py global {set,show,remove,sync}", file=sys.stderr)
        return 1
    if args.cmd == "workmode":
        if args.workmode_cmd == "show":
            return workmode_show()
        if args.workmode_cmd == "set":
            return workmode_set(args.mode)
        print("usage: ns_model_config.py workmode {show,set}", file=sys.stderr)
        return 1
    if args.cmd == "show":
        print("⚠️  'show <project-dir>' is deprecated. Model config is now global.", file=sys.stderr)
        print("   Use: ns_model_config.py global show", file=sys.stderr)
        return 1
    if args.cmd == "validate":
        print("⚠️  'validate <project-dir>' is deprecated. Model config is now global.", file=sys.stderr)
        print("   Use: ns_model_config.py global show  (to inspect current global config)", file=sys.stderr)
        return 1
    if args.cmd == "sync":
        print("⚠️  'sync <project-dir>' is deprecated. Model config is now global.", file=sys.stderr)
        print("   Use: ns_model_config.py global sync  (to sync imported config with current system)", file=sys.stderr)
        return 1

    rows = discover()
    if args.cmd == "list":
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        else:
            print_table(rows)
        return 0

    if args.cmd == "init":
        print("⚠️  'init <project-dir>' is deprecated. Model config is now global for all projects.", file=sys.stderr)
        print("   Use: ns_model_config.py global set", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
