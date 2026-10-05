#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd -- "$repo_root"
command -v codex >/dev/null
command -v python3 >/dev/null
codex --version
python3 - <<'PYTHON'
import os
from pathlib import Path
import subprocess
import sys
import tomllib

if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11+ is required")
home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").resolve()
print(f"CODEX_HOME: {home}")
common = {"model_verbosity": "low", "web_search": "disabled",
          "approval_policy": "on-request", "sandbox_mode": "workspace-write"}
for name, model, effort, enabled in (
    ("lead", "gpt-6.1-sol", "medium", True),
    ("worker", "gpt-6-luna", "medium", False),
    ("mechanical", "gpt-6-luna", "low", False),
):
    path = home / f"{name}.config.toml"
    if not path.is_file() or path.is_symlink():
        raise SystemExit(f"Missing profile or unsafe symlink: {path}")
    with path.open("rb") as handle:
        config = tomllib.load(handle)
    expected = {**common, "model": model, "model_reasoning_effort": effort}
    for key, value in expected.items():
        if config.get(key) != value:
            raise SystemExit(f"{name}: {key} must equal {value!r}")
    agents = config.get("agents", {})
    if agents.get("enabled") is not enabled:
        raise SystemExit(f"{name}: agents.enabled must equal {enabled}")
    if name == "lead":
        defaults = {"default_subagent_model": "gpt-6-luna",
                    "default_subagent_reasoning_effort": "low",
                    "max_concurrent_threads_per_session": 3}
        for key, value in defaults.items():
            if agents.get(key) != value:
                raise SystemExit(f"lead: agents.{key} must equal {value!r}")
    if config.get("service_tier") is not None:
        raise SystemExit(f"{name}: a service tier must not be configured")
    print(f"{path}: exists, valid TOML; model={model}; reasoning={effort}; "
          f"agents.enabled={str(enabled).lower()}")
    print("  verbosity=low; web_search=disabled; sandbox=workspace-write; approval=on-request")
    if name == "lead":
        print("  default subagent=gpt-6-luna; effort=low; spawned-thread limit=3")
    # A runtime command that loads the named profile without calling a model.
    result = subprocess.run(["codex", "--profile", name, "sandbox", "/usr/bin/true"],
                            capture_output=True, text=True, timeout=30)
    if result.returncode:
        # Suppress raw diagnostics: configuration can contain private values.
        raise SystemExit(f"{name}: CLI loading/sandbox check failed (exit {result.returncode}); "
                         "run codex --profile " + name + " sandbox /usr/bin/true to diagnose")
    print(f"  CLI named-profile loading: PASS (no model turn)")
print("PASS: all three profiles match requested settings and load in the CLI.")
print("Scope: saved configuration and CLI loading; live delegated-model execution is untested.")
PYTHON
