"""
TOOL CALLING — ONE TOOL, START TO FINISH
========================================
The whole tool-calling loop in ONE file, top to bottom, no shared helpers.
Read it straight down:

  Step 1  Send the question + the tool definition to the model.
  Step 2  The model reasons, then REQUESTS the tool. (It does NOT run it.)
  Step 3  YOUR code runs the real function.
  Step 4  Send the result back to the model.
  Then    The model writes the final answer, grounded in real data.

The model is the brain. Your code is the hands.

Prereqs: AWS credentials configured, and Bedrock model access for the model
below in us-east-1. The weather function lives in weather.py (plain code, no AI).

Run it:
  python3 tool_calling_demo.py
"""

import json
import boto3

from weather import get_weather  # the real function — plain code, no AI

MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "us-east-1"

bedrock = boto3.client("bedrock-runtime", region_name=REGION)

# ── The tool definition: name, plain-English description, input schema. ──
# This is the ONLY thing the model reads to decide when and how to use it.
# Treat it like a prompt. Note there's no date input — this tool is current-only.
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

QUESTION = "Do I need an umbrella in Toronto today?"
#QUESTION = "what is today's date?"

# Turn on extended thinking so we can SEE the model reason before it acts.
# (Reasoning tokens bill as output tokens, so it costs a little more.)
THINKING = {"thinking": {"type": "enabled", "budget_tokens": 1024}}


print(f"Question: {QUESTION}\n")

# ── STEP 1: send the question + the tool definition to the model. ──
messages = [{"role": "user", "content": [{"text": QUESTION}]}]
print("Step 1: Send question + tool to the model")

response = bedrock.converse(
    modelId=MODEL,
    messages=messages,
    toolConfig={"tools": [WEATHER_TOOL]},
    inferenceConfig={"maxTokens": 2048},
    additionalModelRequestFields=THINKING,
)

# ── STEP 2: the model responds. It reasons, then REQUESTS the tool. ──
assistant_message = response["output"]["message"]
messages.append(assistant_message)  # keep it in the history for the next call

# DEBUG: uncomment to see the full raw model response (see README).
# print(f"ENTIRE MODEL RESPONSE: {assistant_message}")


for block in assistant_message["content"]:
    if "reasoningContent" in block:
        print("\nModel reasoning:")
        print(f"    {block['reasoningContent']['reasoningText']['text']}")

# Grab the tool request, if there is one. It is a REQUEST — nothing has run yet.
tool_request = next(
    (b["toolUse"] for b in assistant_message["content"] if "toolUse" in b), None
)

# The model may decide that NO available tool fits the question. Weather is the
# only tool here, so ask for today's date and you get no request at all. The
# loop stops early. That's an honest limit, and the reason two_tools_demo.py
# and date_injection_demo.py exist.
if tool_request is None:
    answer = "".join(b["text"] for b in assistant_message["content"] if "text" in b)
    print("\nStep 2: Model requested NO tool. None of the tools it was given fit.")
    print(f"\nFinal answer (no tool ran — the model's own limits):\n{answer}")
    raise SystemExit(0)

print(f"\nStep 2: Model requests a tool (not a run): "
      f"{tool_request['name']}({json.dumps(tool_request['input'])})")

# ── STEP 3: YOUR code runs the real function. ──
city = tool_request["input"]["city"]

print(f"Step 3: Run tool: get_weather(city={city!r})")
result = get_weather(city)


# ── STEP 4: send the result back to the model as a toolResult. ──

print(f"Step 4: Return result to model: {json.dumps(result)}")

messages.append(
    {
        "role": "user",
        "content": [
            {
                "toolResult": {
                    "toolUseId": tool_request["toolUseId"],
                    "content": [{"json": result}],
                }
            }
        ],
    }
)

# DEBUG: uncomment to see the full context sent back to the model (see README).
# print(f"ENTIRE CONTEXT {messages}")

# ── The model now writes the final answer, grounded in the real data. ──
final = bedrock.converse(
    modelId=MODEL,
    messages=messages,
    toolConfig={"tools": [WEATHER_TOOL]},
    inferenceConfig={"maxTokens": 2048},
    additionalModelRequestFields=THINKING,
)
answer = "".join(b["text"] for b in final["output"]["message"]["content"] if "text" in b)
print(f"\nFinal answer:\n{answer}")

# DEBUG: uncomment to see the full raw final response (see README).
# print(f"ENTIRE FINAL RESPONSE {final}")