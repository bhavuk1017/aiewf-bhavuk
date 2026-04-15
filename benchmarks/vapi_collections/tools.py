"""Tool schemas for the VAPI Debt Collection Agent benchmark.

These are derived exactly from the VAPI assistant JSON config
(model.tools array), translated into Pipecat FunctionSchema objects.

VAPI config source: model.tools in assistant id d7fefea8-6da3-45fd-a198-d6f848e3cd91
"""

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema

# ---------------------------------------------------------------------------
# 1. recordPayment
# ---------------------------------------------------------------------------
record_payment_function = FunctionSchema(
    name="recordPayment",
    description="Records payment details when customer has already made a payment",
    properties={
        "accountNumber": {
            "type": "string",
            "description": "Customer's account number from context",
        },
        "paymentDate": {
            "type": "string",
            "description": "Date when payment was made (YYYY-MM-DD format)",
        },
        "paymentMode": {
            "type": "string",
            "enum": ["bank_transfer", "upi", "online"],
            "description": "Method of payment used",
        },
        "amount": {
            # VAPI schema natively uses 'number'. Since we are testing against OpenRouter/GPT-4o,
            # proper JSON integer typing works reliably without string coercion.
            "type": "number",
            "description": "Amount paid in rupees",
        },
    },
    required=["accountNumber", "paymentDate", "paymentMode", "amount"],
)

# ---------------------------------------------------------------------------
# 2. createPromiseToPay
# ---------------------------------------------------------------------------
create_promise_to_pay_function = FunctionSchema(
    name="createPromiseToPay",
    description="Creates a payment commitment record when customer promises to pay",
    properties={
        "accountNumber": {
            "type": "string",
            "description": "Customer's account number from context",
        },
        "promiseDate": {
            "type": "string",
            "description": "Date customer commits to pay (YYYY-MM-DD format)",
        },
        "promiseAmount": {
            "type": "number",
            "description": "Amount customer commits to pay in rupees",
        },
        "paymentMode": {
            "type": "string",
            "enum": ["bank_transfer", "upi", "online"],
            "description": "Preferred payment method",
        },
    },
    required=["accountNumber", "promiseDate", "promiseAmount", "paymentMode"],
)

# ---------------------------------------------------------------------------
# 3. transferCall
# ---------------------------------------------------------------------------
transfer_call_function = FunctionSchema(
    name="transferCall",
    description="Transfers the call to a human agent for cases like settlement negotiations, legal mentions, abusive language, or explicit human-agent requests",
    properties={
        "accountNumber": {
            "type": "string",
            "description": "Customer's account number from context",
        },
        "reason": {
            "type": "string",
            "description": "Reason for transferring to human agent (e.g. 'settlement_request', 'legal_mention', 'human_agent_request', 'abusive_language')",
        },
    },
    required=["accountNumber", "reason"],
)

# ---------------------------------------------------------------------------
# 5. scheduleCallback
# ---------------------------------------------------------------------------
schedule_callback_function = FunctionSchema(
    name="scheduleCallback",
    description="Schedules a future callback to the customer",
    properties={
        "accountNumber": {
            "type": "string",
            "description": "Customer's account number from context",
        },
        "callbackDate": {
            "type": "string",
            "description": "Date for callback (YYYY-MM-DD format)",
        },
        "callbackTime": {
            "type": "string",
            "description": "Preferred time for callback",
        },
        "reason": {
            "type": "string",
            "description": "Reason for callback",
        },
    },
    required=["accountNumber", "callbackDate", "reason"],
)

# ---------------------------------------------------------------------------
# Aggregate ToolsSchema (matches VAPI model.tools order)
# Note: endCall is a VAPI built-in with no parameters;
#       it is not required to be declared here since this eval framework
#       tests the LLM tool-calling logic via text pipeline only.
# ---------------------------------------------------------------------------
ToolsSchemaForTest = ToolsSchema(
    standard_tools=[
        record_payment_function,
        create_promise_to_pay_function,
        transfer_call_function,
        schedule_callback_function,
    ]
)
