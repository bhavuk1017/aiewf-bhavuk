"""Configuration for the VAPI Debt Collection Agent benchmark.

Maps to:
  VAPI Assistant: Debt Collection Agent (Production)
  Assistant ID:   d7fefea8-6da3-45fd-a198-d6f848e3cd91
  Model:          gpt-4.1-mini (OpenAI)
  Temperature:    0.2
  Transcriber:    Deepgram nova-3 (multilingual)
  Voice:          Cartesia sonic-3
"""

from benchmarks.vapi_collections.tools import ToolsSchemaForTest
from benchmarks.vapi_collections.turns import turns
from benchmarks.vapi_collections.prompts.system import system_instruction


class BenchmarkConfig:
    """Configuration for the VAPI Debt Collection Agent benchmark."""

    # Benchmark metadata
    name = "vapi_collections"
    description = (
        "HDFC Bank debt collection agent 'Divya' — 4 scenarios covering "
        "payment done, promise to pay, settlement offer, and callback request."
    )

    # Core benchmark data (used by CLI and judge)
    turns = turns
    tools_schema = ToolsSchemaForTest
    first_message = "नमस्ते Chintan जी, मैं Divya बोल रही हूँ HDFC Bank के debt recovery department से। क्या मैं आपसे बात कर रही हूँ?"

    # Exact system instruction from VAPI assistant config
    system_instruction = system_instruction

    # Model config mirroring VAPI (for reference / documentation)
    vapi_model = "gpt-4.1-mini"
    vapi_temperature = 0.2
    vapi_max_tokens = 250
    vapi_provider = "openai"
