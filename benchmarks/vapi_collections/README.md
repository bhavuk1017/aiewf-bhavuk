# VAPI Collections Benchmark

Multi-turn evaluation benchmark for testing a simulated **Vapi debt collection agent** ("Divya", HDFC Bank). Each scenario is an independent conversation that tests tool calling, instruction following, language compliance, and conversational metrics.

## Quick Start

```bash
# Set your API key in .env or environment
export OPENROUTER_API_KEY=sk-or-...

# Run ALL 23 scenarios with GPT-4.1-mini (default), pipeline + judge
python scripts/run_scenarios.py

# Run a specific scenario
python scripts/run_scenarios.py --scenarios scenario_3_settlement

# Run with a different model
python scripts/run_scenarios.py --scenarios scenario_3_settlement --model openai/gpt-4.1

# Dry run — list all scenarios without running
python scripts/run_scenarios.py --dry-run

# Run without judging (transcript only)
python scripts/run_scenarios.py --no-judge

# Export all judged runs to CSV for Google Sheets
python scripts/export_runs.py runs/vapi_collections/
```

## Architecture

```
benchmarks/vapi_collections/
├── README.md                  ← you are here
├── config.py                  ← BenchmarkConfig: wires turns, tools, system prompt
├── prompts/
│   └── system.py              ← Divya's system instruction (verbatim from Vapi config)
├── tools.py                   ← Tool schemas (recordPayment, createPromiseToPay, etc.)
└── turns.py                   ← All 23 scenario definitions

scripts/
├── run_scenarios.py           ← Orchestrator: runs each scenario in isolation, then judges
└── export_runs.py             ← Flattens judged .jsonl into a CSV

src/multi_turn_eval/
├── pipelines/
│   ├── base.py                ← BasePipeline: tool response routing, turn management
│   └── text.py                ← TextPipeline: context aggregation, end-of-turn detection
├── processors/
│   └── tool_call_recorder.py  ← Records tool calls into transcript
└── judging/
    └── claude_judge.py        ← Two-phase LLM judge with realignment
```

### How the Pipeline Works

1. **`run_scenarios.py`** picks a scenario (e.g., `scenario_3_settlement`), creates a fresh `BenchmarkConfig` with that scenario's turns, and launches `TextPipeline`.
2. **`TextPipeline`** sets up the LLM context (system prompt + tools + first user message), then loops: send user turn → LLM responds → record → advance.
3. **Tool calls**: When the LLM calls a tool, `BasePipeline._function_catchall` looks up the response by **function name** from a pre-built map (`_tool_response_map`). This map is built at init by scanning all turns in the scenario for `required_function_call` → `function_call_response` pairs. If the LLM calls a tool not in the map, it gets a default `{"status": "success"}`.
4. **Judging**: After the pipeline finishes, the orchestrator calls `judge_with_claude()` which sends the transcript + golden expectations to an LLM judge (`google/gemini-3.1-pro-preview` via OpenRouter) for two-phase evaluation.

## How to Add a New Scenario

### Step 1: Define the scenario in `turns.py`

Each scenario is a Python list of turn dicts. Add your scenario at the bottom of `benchmarks/vapi_collections/turns.py`:

```python
# =============================================================================
# scenario_my_new_scenario
# =============================================================================

scenario_my_new_scenario = [
    # Turn 0 – User confirms identity
    {
        "input": "Yes, this is Chintan.",
        "golden_text": (
            "Hi Chintan, I'm calling regarding your personal loan — "
            "last four digits six seven eight nine — where twelve thousand rupees "
            "were due on 1st March. Have you already made the payment?"
        ),
        "required_function_call": None,
    },
    # Turn 1 – User says they can't pay
    {
        "input": "I can't pay right now, I need more time.",
        "golden_text": (
            "I understand, let me check if there are any special arrangements..."
        ),
        "required_function_call": {
            "name": "checkSettlementEligibility",
            "args": {"accountNumber": "123456789"},
        },
        "function_call_response": {"eligible": True, "message": "Account qualifies for OTS."},
    },
    # ... more turns
]
```

#### Turn dict schema

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `input` | `str` | ✅ | The simulated user's message (what gets sent to the LLM) |
| `golden_text` | `str` | ✅ | What Divya *should* respond (guidance for the LLM judge) |
| `required_function_call` | `dict \| None` | ✅ | Expected tool call: `{"name": "toolName", "args": {...}}` or `None` |
| `function_call_response` | `dict` | Only if `required_function_call` is set | The mock server response the LLM receives when it calls the tool |

#### Important rules

- **`function_call_response` is matched by function name, not turn index.** If the LLM calls `checkSettlementEligibility` at any turn (not just the one where you defined it), it will receive the response you defined. This handles cases where the LLM calls tools early or late.
- **Each function name should appear at most once per scenario** with a unique response. If the same tool is called twice (e.g., two `createPromiseToPay` calls), both will receive the first defined response.
- **If the LLM calls a tool you didn't define a response for**, it gets `{"status": "success"}` by default.

### Step 2: Register the scenario in `run_scenarios.py`

Add your scenario's variable name to the `ALL_SCENARIOS` list in `scripts/run_scenarios.py`:

```python
ALL_SCENARIOS = [
    "scenario_1_payment_done",
    "scenario_2_promise_to_pay",
    # ... existing scenarios ...
    "scenario_my_new_scenario",   # ← add here
]
```

### Step 3: Run and verify

```bash
# Dry run to confirm it's detected
python scripts/run_scenarios.py --dry-run

# Run just your new scenario
python scripts/run_scenarios.py --scenarios scenario_my_new_scenario

# Check the output
cat runs/vapi_collections/*/transcript.jsonl
```

## Evaluation Dimensions

The LLM judge evaluates each turn on **7 dimensions**:

| Dimension | Type | Description |
|-----------|------|-------------|
| `turn_taking` | bool | Pre-computed from audio analysis (always TRUE for text pipeline) |
| `tool_use_correct` | bool | Did the LLM call the expected tool with correct args? |
| `instruction_following` | bool | Did the response advance the conversation correctly? |
| `kb_grounding` | bool | Are facts (amount, dates, account #) correct? |
| `language_compliance` | bool | Does Divya match the user's language? (Hindi ↔ English) |
| `tool_name_leakage` | bool | TRUE = no leakage (agent didn't say tool names aloud) |
| `tone_and_empathy` | 1-5 | Professional, empathetic tone rating |

### Language compliance rules

- If the user speaks English, Divya **must** respond in English
- If the user speaks Hindi/Hinglish, Divya **must** respond in Hindi
- Evaluated per-turn based on the user's **current** input language
- Mixing English words like "loan", "payment", "UPI" within Hindi is allowed

## Available Scenarios

| # | Name | Turns | Tools Used | Flow |
|---|------|-------|------------|------|
| 1 | `scenario_1_payment_done` | 4 | recordPayment | Happy path: payment already made |
| 2 | `scenario_2_promise_to_pay` | 5 | createPromiseToPay | Promise to pay later (Hindi) |
| 3 | `scenario_3_settlement` | 6 | checkSettlement → offerSettlement → PTP | Refusal → settlement → promise |
| 4 | `scenario_4_callback` | 2 | scheduleCallback | User busy, callback request |
| 5 | `scenario_family_emergency_extension_request` | 5 | scheduleCallback, createPromiseToPay | Family emergency, extension |
| 6 | `scenario_user_not_available_requests_callback` | 4 | scheduleCallback | User in meeting |
| 7 | `scenario_payment_dispute_verification` | 5 | recordPayment | User claims payment done, disputes |
| 8 | `scenario_wrong_number_identification` | 2 | — | Wrong number |
| 9 | `scenario_customer_deceased` | 4 | — | Customer deceased, relative answers |
| 10 | `scenario_user_questions_authenticity` | 5 | createPromiseToPay | User questions caller authenticity |
| 11 | `scenario_user_agrees_immediate_payment` | 4 | createPromiseToPay | Immediate payment |
| 12 | `scenario_customer_disputes_amount_and_penalties` | 6 | checkSettlement → offerSettlement → callback | Amount dispute → settlement offer |
| 13 | `scenario_payment_failed_insufficient_funds` | 5 | createPromiseToPay × 2 | Failed payment, partial payments |
| 14 | `scenario_payment_channel_issue_app_not_working` | 5 | createPromiseToPay | App not working |
| 15 | `scenario_X_multiple_missed_emis_escalation` | 6 | checkSettlement → offerSettlement → PTP | Multiple missed EMIs |
| 16 | `scenario_X_final_warning_before_legal_escalation` | 5 | createPromiseToPay | Final warning before legal |
| 17 | `scenario_X_salary_not_credited_delay` | 5 | createPromiseToPay | Salary delay |
| 18 | `scenario_X_technical_glitch_payment_failure` | 5 | createPromiseToPay | Technical glitch |
| 19 | `scenario_X_payment_deducted_but_status_failed` | 5 | recordPayment | Deducted but failed status |
| 20 | `scenario_X_app_crash_during_payment` | 5 | createPromiseToPay | App crash mid-payment |
| 21 | `scenario_X_otp_not_received` | 5 | createPromiseToPay | OTP not received |
| 22 | `scenario_X_auto_debit_failed` | 5 | createPromiseToPay | Auto-debit mandate failed |
| 23 | `scenario_account_mismatch_issue` | 5 | createPromiseToPay | Account mismatch |

## Output Files

Each scenario run creates a timestamped folder under `runs/vapi_collections/`:

```
runs/vapi_collections/
└── 20260406T183006_scenario_3_settlement_openai_gpt-4.1-mini_b749a01e/
    ├── scenario.txt            # Scenario name for traceability
    ├── transcript.jsonl        # Raw turn-by-turn transcript
    ├── runtime.json            # Run metadata and timing
    ├── claude_judged.jsonl     # Per-turn judgments with scores + reasoning
    ├── claude_summary.json     # Aggregate score metrics
    └── claude_analysis.md      # Human-readable failure report
```
