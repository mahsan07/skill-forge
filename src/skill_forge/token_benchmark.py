"""Token-compression benchmark runner for Skill Forge."""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


def estimate_tokens(text: str) -> int:
    """Return a transparent, model-neutral comparison estimate."""
    if not text:
        return 0
    return max(1, (len(text.encode("utf-8")) + 3) // 4)


def reduction_pct(before: int, after: int) -> float:
    if before <= 0:
        return 0.0
    return round((before - after) * 100.0 / before, 2)


def _render_command(parts: list[str], *, source_command: str, input_file: str = "") -> list[str]:
    values = {"source_command": source_command, "input_file": input_file}
    return [part.format(**values) for part in parts]


def _run_adapter(adapter: dict[str, Any], fixture: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    kind = adapter.get("kind")
    text = fixture["text"]
    source_command = fixture.get("source_command", "")
    timeout_s = float(adapter.get("timeout_s", 60))

    if kind == "identity":
        return text, {"returncode": 0, "stderr": ""}

    command = adapter.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(part, str) for part in command):
        raise ValueError("external adapters require a non-empty string-list command")

    if kind == "stdin_command":
        result = subprocess.run(
            _render_command(command, source_command=source_command),
            input=text,
            text=True,
            capture_output=True,
            timeout=timeout_s,
            check=False,
        )
        return result.stdout, {"returncode": result.returncode, "stderr": result.stderr.strip()}

    if kind == "file_rewrite_command":
        suffix = fixture.get("suffix", ".md")
        with tempfile.TemporaryDirectory(prefix="skill-forge-token-bench-") as temporary:
            input_path = Path(temporary) / f"input{suffix}"
            input_path.write_text(text, encoding="utf-8")
            result = subprocess.run(
                _render_command(command, source_command=source_command, input_file=str(input_path)),
                text=True,
                capture_output=True,
                timeout=timeout_s,
                check=False,
            )
            rewritten = input_path.read_text(encoding="utf-8")
            return rewritten, {"returncode": result.returncode, "stderr": result.stderr.strip()}

    raise ValueError(f"unsupported adapter kind: {kind!r}")


def _validate_fixture(fixture: dict[str, Any]) -> None:
    for key in ("id", "text"):
        if not isinstance(fixture.get(key), str) or not fixture[key].strip():
            raise ValueError(f"fixture {key} must be a non-empty string")
    must_contain = fixture.get("must_contain", [])
    if not isinstance(must_contain, list) or not all(isinstance(item, str) and item for item in must_contain):
        raise ValueError("fixture must_contain must be a list of non-empty strings")


def _validate_adapter(name: str, adapter: dict[str, Any]) -> None:
    if not isinstance(adapter, dict):
        raise ValueError(f"adapter {name!r} must be an object")
    if adapter.get("kind") not in {"identity", "stdin_command", "file_rewrite_command"}:
        raise ValueError(f"adapter {name!r} has unsupported kind")


def run_benchmark(fixtures: list[dict[str, Any]], adapters: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Run all enabled adapters against all fixtures and return a JSON-ready receipt."""
    if not fixtures:
        raise ValueError("at least one fixture is required")
    if not adapters:
        raise ValueError("at least one adapter is required")

    for fixture in fixtures:
        _validate_fixture(fixture)
    for name, adapter in adapters.items():
        _validate_adapter(name, adapter)

    runs: list[dict[str, Any]] = []
    for adapter_name, adapter in adapters.items():
        if adapter.get("enabled", True) is False:
            continue
        for fixture in fixtures:
            before_text = fixture["text"]
            started = time.perf_counter()
            try:
                after_text, process = _run_adapter(adapter, fixture)
                error = None
            except (OSError, subprocess.SubprocessError, ValueError) as exc:
                after_text = ""
                process = {"returncode": None, "stderr": ""}
                error = str(exc)
            latency_ms = round((time.perf_counter() - started) * 1000.0, 2)

            must_contain = fixture.get("must_contain", [])
            preserved = [item for item in must_contain if item in after_text]
            missing = [item for item in must_contain if item not in after_text]

            before_bytes = len(before_text.encode("utf-8"))
            after_bytes = len(after_text.encode("utf-8"))
            before_tokens = estimate_tokens(before_text)
            after_tokens = estimate_tokens(after_text)

            runs.append(
                {
                    "adapter": adapter_name,
                    "fixture_id": fixture["id"],
                    "direction": fixture.get("direction", "input"),
                    "status": "pass" if error is None and process["returncode"] == 0 and not missing else "fail",
                    "error": error,
                    "process_returncode": process["returncode"],
                    "process_stderr": process["stderr"],
                    "latency_ms": latency_ms,
                    "bytes_before": before_bytes,
                    "bytes_after": after_bytes,
                    "byte_reduction_pct": reduction_pct(before_bytes, after_bytes),
                    "estimated_tokens_before": before_tokens,
                    "estimated_tokens_after": after_tokens,
                    "estimated_token_reduction_pct": reduction_pct(before_tokens, after_tokens),
                    "critical_facts_total": len(must_contain),
                    "critical_facts_preserved": len(preserved),
                    "critical_fact_retention_pct": round(
                        (len(preserved) * 100.0 / len(must_contain)) if must_contain else 100.0,
                        2,
                    ),
                    "missing_critical_facts": missing,
                    "non_expanding": after_bytes <= before_bytes,
                }
            )

    summary: dict[str, Any] = {}
    for adapter_name in sorted({run["adapter"] for run in runs}):
        subset = [run for run in runs if run["adapter"] == adapter_name]
        passed = [run for run in subset if run["status"] == "pass"]
        summary[adapter_name] = {
            "runs": len(subset),
            "passes": len(passed),
            "failures": len(subset) - len(passed),
            "all_critical_facts_preserved": all(not run["missing_critical_facts"] for run in subset),
            "mean_estimated_token_reduction_pct": round(
                sum(run["estimated_token_reduction_pct"] for run in subset) / len(subset), 2
            ),
        }

    return {
        "protocol_version": "0.1",
        "benchmark": "token-compression",
        "measurement_note": (
            "estimated_tokens use a provider-neutral four-UTF-8-bytes-per-token comparison unit; "
            "they are not provider billing tokens"
        ),
        "runs": runs,
        "summary": summary,
    }


def run_benchmark_files(fixtures_path: str | Path, adapters_path: str | Path) -> dict[str, Any]:
    fixtures_doc = json.loads(Path(fixtures_path).read_text(encoding="utf-8"))
    adapters_doc = json.loads(Path(adapters_path).read_text(encoding="utf-8"))
    fixtures = fixtures_doc["fixtures"] if isinstance(fixtures_doc, dict) else fixtures_doc
    adapters = adapters_doc["adapters"] if isinstance(adapters_doc, dict) else adapters_doc
    if not isinstance(fixtures, list):
        raise ValueError("fixtures document must contain a fixtures list")
    if not isinstance(adapters, dict):
        raise ValueError("adapters document must contain an adapters object")
    return run_benchmark(fixtures, adapters)
