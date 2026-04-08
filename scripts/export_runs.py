#!/usr/bin/env python3
"""
Export eval runs to a structured CSV for Google Sheets.

Reads claude_judged.jsonl from one or all timestamped run folders and outputs
a flat CSV with one row per turn: turn metadata, user/assistant text, tool
calls, and all judge scores + reasoning.

Usage:
    # Export a single run folder
    python scripts/export_runs.py runs/vapi_collections/20260403T003654_openai_gpt-4.1-mini_017556bc/

    # Export ALL run folders under a benchmark
    python scripts/export_runs.py runs/vapi_collections/

    # Export to a specific output file
    python scripts/export_runs.py runs/vapi_collections/ --output my_report.csv
"""

import json
import csv
import sys
import argparse
from pathlib import Path


SCORE_COLS = [
    "turn_taking",
    "tool_use_correct",
    "instruction_following",
    "kb_grounding",
    "language_compliance",
    "tool_name_leakage",
    "tone_and_empathy",
]

CSV_COLUMNS = [
    "run_folder",
    "model",
    "turn",
    "timestamp",
    "latency_ms",
    # Conversation
    "user_text",
    "assistant_text",
    "tool_calls",
    "tool_results",
    # Token usage
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    # Judge scores
    "turn_taking",
    "tool_use_correct",
    "instruction_following",
    "kb_grounding",
    "language_compliance",
    "tool_name_leakage",
    "tone_and_empathy",
    "all_pass",
    "claude_reasoning",
]


def bool_to_symbol(val):
    if isinstance(val, bool):
        return "✅" if val else "❌"
    return str(val)


def format_tool_calls(tool_calls: list) -> str:
    if not tool_calls:
        return ""
    parts = []
    for tc in tool_calls:
        name = tc.get("name", "?")
        args = tc.get("args", {})
        parts.append(f"{name}({json.dumps(args, ensure_ascii=False)})")
    return " | ".join(parts)


def format_tool_results(tool_results: list) -> str:
    if not tool_results:
        return ""
    parts = []
    for tr in tool_results:
        name = tr.get("name", "?")
        result = tr.get("response", {}).get("result", {})
        parts.append(f"{name} → {json.dumps(result, ensure_ascii=False)}")
    return " | ".join(parts)


def find_judged_files(root: Path) -> list[Path]:
    """Find all claude_judged.jsonl files under root."""
    # If root itself contains claude_judged.jsonl, treat as single run folder
    single = root / "claude_judged.jsonl"
    if single.exists():
        return [single]
    # Otherwise search one level deep (each timestamped subfolder)
    return sorted(root.glob("*/claude_judged.jsonl"))


def process_file(judged_path: Path, writer: csv.DictWriter, scenario_num: int):
    run_folder = judged_path.parent.name

    # Write a blank separator row then a scenario header row
    blank = {col: "" for col in CSV_COLUMNS}
    writer.writerow(blank)
    header = {col: "" for col in CSV_COLUMNS}
    header["run_folder"] = f"=== Scenario {scenario_num}: {run_folder} ==="
    writer.writerow(header)

    with open(judged_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    for line in lines:
        turn = json.loads(line)
        scores = turn.get("scores", {})

        # Compute overall pass: all booleans must be True, tone >= 4
        bool_scores = [v for k, v in scores.items() if isinstance(v, bool)]
        tone = scores.get("tone_and_empathy", 0)
        all_pass = all(bool_scores) and tone >= 4

        row = {
            "run_folder": run_folder,
            "model": turn.get("model_name", ""),
            "turn": turn.get("turn", ""),
            "timestamp": turn.get("ts", ""),
            "latency_ms": turn.get("latency_ms", ""),
            "user_text": turn.get("user_text", ""),
            "assistant_text": turn.get("assistant_text", ""),
            "tool_calls": format_tool_calls(turn.get("tool_calls", [])),
            "tool_results": format_tool_results(turn.get("tool_results", [])),
            "prompt_tokens": turn.get("tokens", {}).get("prompt_tokens", ""),
            "completion_tokens": turn.get("tokens", {}).get("completion_tokens", ""),
            "total_tokens": turn.get("tokens", {}).get("total_tokens", ""),
            # Judge scores
            "turn_taking": bool_to_symbol(scores.get("turn_taking")),
            "tool_use_correct": bool_to_symbol(scores.get("tool_use_correct")),
            "instruction_following": bool_to_symbol(scores.get("instruction_following")),
            "kb_grounding": bool_to_symbol(scores.get("kb_grounding")),
            "language_compliance": bool_to_symbol(scores.get("language_compliance")),
            "tool_name_leakage": bool_to_symbol(scores.get("tool_name_leakage")),
            "tone_and_empathy": scores.get("tone_and_empathy", ""),
            "all_pass": "✅" if all_pass else "❌",
            "claude_reasoning": turn.get("claude_reasoning", ""),
        }

        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="Export aiewf-eval runs to CSV")
    parser.add_argument(
        "path",
        type=Path,
        help="Path to a single run folder OR a benchmark folder containing multiple runs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output CSV file path (default: <benchmark>_export.csv next to input)",
    )
    args = parser.parse_args()

    root = args.path.resolve()
    if not root.exists():
        print(f"ERROR: Path does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    judged_files = find_judged_files(root)
    if not judged_files:
        print(f"ERROR: No claude_judged.jsonl files found under {root}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output or root.parent / f"{root.name}_export.csv"

    with open(output_path, "w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=CSV_COLUMNS)
        writer.writeheader()

        for scenario_num, judged_path in enumerate(judged_files, start=1):
            print(f"Processing Scenario {scenario_num}: {judged_path.parent.name}")
            process_file(judged_path, writer, scenario_num)

    print(f"\n✅ Exported {len(judged_files)} run(s) → {output_path}")


if __name__ == "__main__":
    main()
