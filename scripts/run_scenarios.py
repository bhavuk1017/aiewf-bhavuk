#!/usr/bin/env python3
"""
Multi-scenario orchestrator for vapi_collections benchmark.

Runs each scenario in full isolation (independent LLM context) then judges it.
Scenarios are sourced directly from benchmarks/vapi_collections/turns.py.

Usage:
    # Run ALL scenarios:
    uv run python scripts/run_scenarios.py

    # Run specific scenarios by name:
    uv run python scripts/run_scenarios.py --scenarios scenario_2_promise_to_pay scenario_3_settlement

    # Run with a different model:
    uv run python scripts/run_scenarios.py --model openai/gpt-4o --service openrouter

    # Run without judging (transcripts only):
    uv run python scripts/run_scenarios.py --no-judge

    # Dry run (just list scenarios without running):
    uv run python scripts/run_scenarios.py --dry-run
"""

import argparse
import asyncio
import importlib
import json
import sys
from pathlib import Path
from datetime import datetime
import uuid

from dotenv import load_dotenv

# Load .env so OPENROUTER_API_KEY etc. are available without manual export
load_dotenv()

# ---------------------------------------------------------------------------
# All known scenarios in turns.py — update this list as you add more
# ---------------------------------------------------------------------------
ALL_SCENARIOS = [
    "scenario_1_payment_done",
    "scenario_2_promise_to_pay",
    "scenario_3_settlement",
    "scenario_4_callback",
    "scenario_family_emergency_extension_request",
    "scenario_user_not_available_requests_callback",
    "scenario_payment_dispute_verification",
    "scenario_wrong_number_identification",
    "scenario_customer_deceased",
    "scenario_user_questions_authenticity",
    "scenario_user_agrees_immediate_payment",
    "scenario_customer_disputes_amount_and_penalties",
    "scenario_payment_failed_insufficient_funds",
    "scenario_payment_channel_issue_app_not_working",
    "scenario_X_multiple_missed_emis_escalation",
    "scenario_X_final_warning_before_legal_escalation",
    "scenario_X_salary_not_credited_delay",
    "scenario_X_technical_glitch_payment_failure",
    "scenario_X_payment_deducted_but_status_failed",
    "scenario_X_app_crash_during_payment",
    "scenario_X_otp_not_received",
    "scenario_X_auto_debit_failed",
    "scenario_account_mismatch_issue",
]


def get_scenario_list(requested: list[str] | None) -> list[str]:
    """Validate and return the scenarios to run."""
    turns_module = importlib.import_module("benchmarks.vapi_collections.turns")
    available = [name for name in ALL_SCENARIOS if hasattr(turns_module, name)]

    if not requested:
        return available

    invalid = [s for s in requested if not hasattr(turns_module, s)]
    if invalid:
        print(f"ERROR: Unknown scenario(s): {invalid}")
        print(f"Available: {available}")
        sys.exit(1)

    return requested


async def run_scenario(
    scenario_name: str,
    turns: list,
    model: str,
    service_name: str,
    run_judge: bool,
    verbose: bool,
) -> dict:
    """
    Run a single scenario end-to-end: pipeline + optional judging.
    Returns a summary dict with the run directory and pass/fail info.
    """
    from benchmarks.vapi_collections.config import BenchmarkConfig
    from multi_turn_eval.pipelines.text import TextPipeline
    from multi_turn_eval.recording.transcript_recorder import TranscriptRecorder
    from pipecat.services.openai.llm import OpenAILLMService

    # Patch turns for this scenario only
    benchmark = BenchmarkConfig()
    benchmark.turns = turns

    # Create a labelled run directory
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    safe_model = model.replace("/", "_").replace(":", "_")
    suffix = str(uuid.uuid4())[:8]
    run_dir = Path("runs") / "vapi_collections" / f"{timestamp}_{scenario_name}_{safe_model}_{suffix}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Write scenario name into run dir for traceability
    (run_dir / "scenario.txt").write_text(scenario_name)

    print(f"\n{'='*70}")
    print(f"  SCENARIO: {scenario_name}")
    print(f"  Turns:    {len(turns)}")
    print(f"  Output:   {run_dir}")
    print(f"{'='*70}")

    recorder = TranscriptRecorder(run_dir, model)

    try:
        pipeline = TextPipeline(benchmark)
        await pipeline.run(
            recorder=recorder,
            model=model,
            service_class=OpenAILLMService,
            service_name=service_name,
            turn_indices=None,
        )
        print(f"  ✅ Pipeline complete")
    except Exception as e:
        print(f"  ❌ Pipeline error: {e}")
        return {"scenario": scenario_name, "run_dir": str(run_dir), "error": str(e)}
    finally:
        recorder.close()

    if not run_judge:
        return {"scenario": scenario_name, "run_dir": str(run_dir)}

    # -------------------------
    # Judge
    # -------------------------
    print(f"  Judging...")
    try:
        from multi_turn_eval.judging.claude_judge import judge_with_claude, load_transcript, write_outputs

        result = await judge_with_claude(
            run_dir,
            only_turns=None,
            debug=verbose,
            expected_turns=turns,
        )

        records = load_transcript(run_dir)
        write_outputs(
            run_dir,
            records,
            result["judgments"],
            result["summary"],
            result["model_name"],
            result.get("realignment_notes", ""),
            result.get("function_tracking", {}),
            result.get("turn_taking_analysis"),
        )

        # Compute pass counts directly from judgments (summary is a plain string)
        judgments = result["judgments"]
        total = len(judgments)
        score_keys = ["turn_taking", "tool_use_correct", "instruction_following",
                      "kb_grounding", "language_compliance", "tool_name_leakage"]
        passes = {}
        for key in score_keys:
            passes[key] = sum(
                1 for j in judgments.values()
                if j.get("scores", {}).get(key, False)
            )
        # tone_and_empathy: count turns with score >= 4
        passes["tone_and_empathy"] = sum(
            1 for j in judgments.values()
            if j.get("scores", {}).get("tone_and_empathy", 0) >= 4
        )

        print(f"  Judged {total} turns:")
        print(f"    Turn-taking:          {passes.get('turn_taking', 0)}/{total}")
        print(f"    Tool use:             {passes.get('tool_use_correct', 0)}/{total}")
        print(f"    Instruction following:{passes.get('instruction_following', 0)}/{total}")
        print(f"    KB grounding:         {passes.get('kb_grounding', 0)}/{total}")
        print(f"    Language compliance:  {passes.get('language_compliance', 0)}/{total}")
        print(f"  ✅ Judging complete → {run_dir / 'claude_judged.jsonl'}")

        return {
            "scenario": scenario_name,
            "run_dir": str(run_dir),
            "passes": passes,
            "total_turns": total,
        }

    except Exception as e:
        print(f"  ❌ Judging error: {e}")
        return {"scenario": scenario_name, "run_dir": str(run_dir), "judge_error": str(e)}


async def main_async(args):
    import benchmarks.vapi_collections.turns as turns_module

    scenarios = get_scenario_list(args.scenarios or None)

    if args.dry_run:
        print(f"Would run {len(scenarios)} scenario(s):")
        for s in scenarios:
            turns = getattr(turns_module, s)
            print(f"  {s} ({len(turns)} turns)")
        return

    print(f"\nRunning {len(scenarios)} scenario(s) with model: {args.model}")
    print(f"Judge: {'enabled' if not args.no_judge else 'disabled'}")

    results = []
    for scenario_name in scenarios:
        turns = getattr(turns_module, scenario_name)
        result = await run_scenario(
            scenario_name=scenario_name,
            turns=turns,
            model=args.model,
            service_name=args.service,
            run_judge=not args.no_judge,
            verbose=args.verbose,
        )
        results.append(result)

    # -------------------------
    # Final summary
    # -------------------------
    print(f"\n{'='*70}")
    print(f"  FINAL SUMMARY — {len(results)} scenario(s)")
    print(f"{'='*70}")
    for r in results:
        name = r["scenario"]
        if "error" in r:
            print(f"  ❌ {name}: pipeline error — {r['error']}")
        elif "judge_error" in r:
            print(f"  ⚠️  {name}: judging error — {r['judge_error']}")
        elif "passes" in r:
            p = r["passes"]
            t = r["total_turns"]
            print(
                f"  {'✅' if all(v == t for v in p.values() if isinstance(v, int)) else '⚠️ '} "
                f"{name}: "
                f"tool={p.get('tool_use_correct',0)}/{t} "
                f"instr={p.get('instruction_following',0)}/{t} "
                f"lang={p.get('language_compliance',0)}/{t}"
            )
        else:
            print(f"  ✅ {name}: transcript saved → {r['run_dir']}")

    # Write a combined summary JSON next to the runs folder
    summary_path = Path("runs") / "vapi_collections" / f"batch_{datetime.now().strftime('%Y%m%dT%H%M%S')}_summary.json"
    summary_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n  Batch summary → {summary_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Run vapi_collections scenarios independently with full context isolation."
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        metavar="SCENARIO_NAME",
        help="Specific scenario variable names to run (default: all). "
             "E.g., --scenarios scenario_2_promise_to_pay scenario_3_settlement",
    )
    parser.add_argument(
        "--model",
        default="openai/gpt-4.1-mini",
        help="Model name for OpenRouter (default: openai/gpt-4.1-mini)",
    )
    parser.add_argument(
        "--service",
        default="openrouter",
        help="Service backend (default: openrouter)",
    )
    parser.add_argument(
        "--no-judge",
        action="store_true",
        help="Skip the judging step (only run pipeline)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List which scenarios would run without actually running them",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose logging",
    )

    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
