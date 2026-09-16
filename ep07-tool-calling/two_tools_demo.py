"""
TWO TOOLS — THE LOOP
====================
One tool was a straight line (see tool_calling_demo.py). With more than one
tool, you don't know in advance which the model will call, or how many times.
So the four steps go inside a LOOP: send, let the model request tool(s), run
them, send the results back, repeat — until the model stops asking and answers.

Same four steps, now repeating:
  Step 1  Send the question + the tool definitions.
  Step 2  Model reasons, then requests one or more tools (or writes the answer).
  Step 3  Your code runs each requested tool.
  Step 4  Send the results back. Loop.

This file is self-contained. The two real functions live in weather.py and
datetime_tool.py (plain code, no AI).

Run it:
  python3 two_tools_demo.py
"""

import json
import boto3

from weather import get_weather
from datetime_tool import get_current_datetime

MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "us-east-1"

bedrock = boto3.client("bedrock-runtime", region_name=REGION)

# ── Two tool definitions. ──
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

DATETIME_TOOL = {
    "toolSpec": {
        "name": "get_current_datetime",
        "description": "Get the current date and time. Use for questions about the day, date, or time. Takes no arguments.",
        "inputSchema": {"json": {"type": "object", "properties": {}}},
    }
}

# name → the real function to run when the model asks for it.
TOOLS = {
    "get_weather": get_weather,
    "get_current_datetime": get_current_datetime,
}

QUESTION = "Do I need an umbrella in Toronto? And what is today's date?"

# Extended thinking on, so we can see the model reason each turn.
THINKING = {"thinking": {"type": "enabled", "budget_tokens": 1024}}


print(f"Question: {QUESTION}\n")

messages = [{"role": "user", "content": [{"text": QUESTION}]}]
print("Step 1: Send question + tools to the model\n")

# ── The loop: keep going while the model keeps asking for tools. ──
while True:
    response = bedrock.converse(
        modelId=MODEL,
        messages=messages,
        toolConfig={"tools": [WEATHER_TOOL, DATETIME_TOOL]},
        inferenceConfig={"maxTokens": 2048},
        additionalModelRequestFields=THINKING,
    )

    assistant_message = response["output"]["message"]
    messages.append(assistant_message)

    # DEBUG: uncomment to see the full raw model response each turn (see README).
    # print()
    # print(f"ENTIRE MODEL RESPONSE: {response}")
    # print()

    # Step 2: show the model's reasoning for this turn.
    for block in assistant_message["content"]:
        if "reasoningContent" in block:
            print("Model reasoning:")
            print(f"    {block['reasoningContent']['reasoningText']['text']}")

    # Done? The model stopped asking for tools and wrote its answer.
    if response["stopReason"] != "tool_use":
        answer = "".join(b["text"] for b in assistant_message["content"] if "text" in b)
        print(f"\nFinal answer:\n{answer}")
        print()
        print()
        # DEBUG: uncomment to see the full raw final response (see README).
        # print(f"ENTIRE FINAL RESPONSE {response}")
        break

    # Otherwise: run every tool the model requested, collect the results.
    tool_results = []
    for block in assistant_message["content"]:
        if "toolUse" not in block:
            continue
        request = block["toolUse"]
        args = request["input"]

        # Step 2: the request (nothing has run yet).
        print()
        print(f"Step 2: Model requests a tool (not a run): {request['name']}({json.dumps(args)})")

        # Step 3: your code runs the real function.
        result = TOOLS[request["name"]](**args)
        call = ", ".join(f"{k}={v!r}" for k, v in args.items())
        print(f"Step 3: Run tool: {request['name']}({call})")

        # Step 4: package the result to send back.
        print(f"Step 4: Return result to model: {json.dumps(result)}")
        tool_results.append(
            {
                "toolResult": {
                    "toolUseId": request["toolUseId"],
                    "content": [{"json": result}],
                }
            }
        )

    messages.append({"role": "user", "content": tool_results})
    # DEBUG: uncomment to see the full context sent back to the model each loop (see README).
    # print()
    # print(f"ENTIRE CONTEXT sent to model again: {messages}")
    # print()
