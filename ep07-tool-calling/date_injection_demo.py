"""
HOW THE APPS KNOW THE DATE — INJECTION, NOT A TOOL
==================================================
A raw model doesn't know today's date. Yet ChatGPT and Claude answer "what's
today's date?" instantly. They don't call a tool. They paste it in.

Anthropic publishes Claude's system prompt in their release notes, and it
contains a line like: "The current date is {{currentDateTime}}." The app fills
that in fresh every conversation. No tool runs — it's just text added before
your message.
  Docs: https://platform.claude.com/docs/en/release-notes/system-prompts

This file proves it. We offer only the weather tool (NO date tool), but slip
today's date into the system prompt. Ask for the date and the model answers
correctly with NO tool call, because it was handed the date as context.

Contrast:
  two_tools_demo.py       → the model CALLS a get_current_datetime tool.
  date_injection_demo.py  → no date tool; the date is injected as context.
Two ways to hand the model the same fact.

Run it:
  python3 date_injection_demo.py
"""

import json
import boto3

from datetime_tool import get_current_datetime  # used only to fill the prompt

MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "us-east-1"

bedrock = boto3.client("bedrock-runtime", region_name=REGION)

# The weather tool is available, but there is NO date tool here on purpose.
WEATHER_TOOL = {
    "toolSpec": {
        "name": "get_weather",
        "description": "Get the CURRENT weather for a single city. Cannot forecast future dates.",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "A single city name, e.g. 'Toronto'."}
                },
                "required": ["city"],
            }
        },
    }
}

# Slip today's date into the system prompt as plain text — the same trick the
# chat apps use. Nothing "looks it up"; it's just context handed to the model.
now = get_current_datetime()
SYSTEM_PROMPT = f"The current date is {now['day_of_week']}, {now['date']}."

QUESTION = "What's today's date?"

THINKING = {"thinking": {"type": "enabled", "budget_tokens": 1024}}


print(f"Question: {QUESTION}")
print(f'(system prompt: "{SYSTEM_PROMPT}")\n')

# One call. The date is in the system prompt, so no tool is needed.
messages = [{"role": "user", "content": [{"text": QUESTION}]}]
print("Step 1: Send question + tool + system prompt (with the date) to the model\n")

response = bedrock.converse(
    modelId=MODEL,
    messages=messages,
    system=[{"text": SYSTEM_PROMPT}],
    toolConfig={"tools": [WEATHER_TOOL]},
    inferenceConfig={"maxTokens": 2048},
    additionalModelRequestFields=THINKING,
)

# DEBUG: uncomment to see the full raw model response (see README).
# print(f"ENTIRE CONTEXT: {response}")

assistant_message = response["output"]["message"]

for block in assistant_message["content"]:
    if "reasoningContent" in block:
        print("Model reasoning:")
        print(f"    {block['reasoningContent']['reasoningText']['text']}")

# No tool request — the model answers straight from the injected date.
answer = "".join(b["text"] for b in assistant_message["content"] if "text" in b)
print(f"\nFinal answer (no tool call — used the injected date):\n{answer}")
