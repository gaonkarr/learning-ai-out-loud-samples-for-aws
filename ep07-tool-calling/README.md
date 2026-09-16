# Episode 7: When AI picks up tools (tool calling + MCP)

For the last two episodes, the model could read your documents and answer from them. But it still couldn't *do* anything. It couldn't tell you if it was going to rain, and it couldn't even tell you what today's date is, because a foundation model on its own is frozen at its training cutoff and locked in a box: text in, text out.

This folder gives it a way out. Two small tools — a live weather lookup and a current date/time lookup — wired to [Amazon Bedrock](https://aws.amazon.com/bedrock?trk=44b16281-e090-49b6-97d8-f1cea54d9e87&sc_channel=el) via the Converse API's `toolConfig`. Everything here works. There's no contrived failure. The honest limit shows up on its own: ask the model something no tool covers and it can't answer.

**The one thing most people get wrong:** the model does NOT run the tool. It only asks to. The model reads your question, decides a tool is needed, and hands back a structured request. Your code runs the real function and hands the result back. The model is the brain; your code is the hands.

## 📺 Watch and/or read

This repo is the code companion for Episode 7 of *Learning AI Out Loud*. The video and blog walk through the *why*. This README covers the *how* of running it.

- 🎥 **Video:** [How AI actually calls an API — tool calling explained from scratch](https://youtu.be/mCnsIHja5cw)
- 📝 **Blog (dev.to):** [How AI actually calls an API — tool calling explained from scratch](https://dev.to/rohini_gaonkar/how-ai-actually-calls-an-api-tool-calling-explained-from-scratch-4lf8)
- 📝 **Blog (AWS Builder Center):** [How AI actually calls an API — tool calling explained from scratch](https://builder.aws.com/content/3JQXxclnjAEFozjqf5LiLXgafrK/how-ai-actually-calls-an-api-tool-calling-explained-from-scratch)
- 📺 **Series playlist:** [Learning AI Out Loud](https://www.youtube.com/playlist?list=PLTuh5MoXKZTwoeROV-bA4_6maw0FIoeEf)
- ⬅️ **Previous:** [Episode 6 — why RAG gives wrong answers](../ep06-rag-failures/)

## The four-step loop

Every demo runs the same four steps. Each file is self-contained (no shared
helper) so you can read it top to bottom:

1. **Send** the question + the tool definitions to the model.
2. The model **decides**: answer directly, or reply with a structured tool-call request.
3. **Your code runs** the real function the model asked for.
4. **Send the result back.** Now the model writes the final answer, grounded in real data.

`tool_calling_demo.py` shows this as a straight line for one tool.
`two_tools_demo.py` puts the same four steps inside a loop, because with more
than one tool you don't know which the model will call, or how many times.

The model chooses both the tool *and* its arguments.

## What runs

```bash
python3 tool_calling_demo.py    # ONE TOOL:   weather. Clean question → grounded answer.
python3 two_tools_demo.py       # TWO TOOLS:  weather + date. Model picks the right one per need.
python3 date_injection_demo.py  # NO DATE TOOL: date slipped into the system prompt instead.
```

You can also run each tool on its own — no AWS needed — to confirm they work before a shoot:

```bash
python3 weather.py
python3 datetime_tool.py
```

> **Want to see the raw API traffic?** Each demo has a few `# DEBUG:` lines
> commented out (the full `ENTIRE MODEL RESPONSE`, `ENTIRE CONTEXT`, and
> `ENTIRE FINAL RESPONSE` dumps). By default the output stays clean and matches
> what you see below. Uncomment those lines in any demo to print the complete
> raw request and response payloads and watch exactly what goes to and from the
> model.

### 1. One tool works — `tool_calling_demo.py`

Ask something the model provably can't know on its own. The output is labelled by the four-step loop so you can follow along. Extended thinking is on, so you also see the model reason before it acts:

```
Question: Do I need an umbrella in Toronto today?

Step 1: Send question + tools to the model

Model reasoning:
    The user wants current weather in Toronto. I have a get_weather tool;
    I'll call it with city = Toronto.
Step 2: Model requests a tool (not a run): get_weather({"city": "Toronto"})
Step 3: Run tool: get_weather(city='Toronto')
Step 4: Return result to model: {"city": "Toronto", "country": "Canada", "temperature_c": 12.3, "conditions": "light rain", "wind_kph": 14.0}

Final answer:
Yes — it's raining in Toronto right now, around 12°C. Bring an umbrella.
```

That answer did not exist in the model. It came from a live API, fetched because the model asked for it, run by your code, and read back to the model.

The demo question also asks for today's date. There's no date tool here — only weather — so the model tells you it doesn't know the date. That's the honest limit, and it's the whole reason for the next step.

### 2. Two tools — `two_tools_demo.py`

Give the model a second tool (`get_current_datetime`) and ask something that needs both:

```
Question: What's today's date, and do I need an umbrella in Toronto?

Step 1: Send question + tools to the model

Model reasoning:
    Two things asked: the date and the weather. I have both tools;
    I'll call get_current_datetime and get_weather.
Step 2: Model requests a tool (not a run): get_current_datetime({})
Step 3: Run tool: get_current_datetime()
Step 4: Return result to model: {"date": "2026-07-27", "day_of_week": "Monday", "time": "14:05", ...}
Step 2: Model requests a tool (not a run): get_weather({"city": "Toronto"})
Step 3: Run tool: get_weather(city='Toronto')
Step 4: Return result to model: {"city": "Toronto", "conditions": "light rain", ...}

Final answer:
Today is Monday, July 27, 2026. And yes — it's raining in Toronto, bring an umbrella.
```

The model read the question, saw it needed two different things, and asked for both tools. Your code ran each. The model picks *which* tool fits *which* part of the question.

> **Why can't the weather tool tell me about next week?** Look at its schema: the only argument is `city`, and it returns current conditions. There's no date parameter, and it can't forecast. That's the tool's contract, not a bug. If you want next week, that's a *different* tool.

### 3. How the apps know the date — `date_injection_demo.py`

If a raw model doesn't know the date, how does ChatGPT or Claude answer "what's today's date?" instantly? They don't call a tool. They **paste it in**.

Anthropic actually publishes Claude's system prompt in their release notes, and it contains a line like `The current date is {{currentDateTime}}`. The app fills that in fresh every conversation. No tool runs — it's just text added before your message. ([Claude system prompts docs](https://platform.claude.com/docs/en/release-notes/system-prompts).)

This demo proves it. We offer **no date tool** — only weather is available — but slip today's date into the system prompt. Ask for the date and the model answers correctly with **no tool call**, because it was handed the date as context.

```
Question: What's today's date?
  (system prompt: "The current date is Monday, 2026-07-27.")

Step 1: Send question + tools to the model

Model reasoning:
    I already have today's date from the context; no tool needed.

Final answer:
Today is Monday, July 27, 2026.
(no tool request — answered straight from the injected context)
```

Two different ways to hand the model the same fact: build a **tool** and let it ask (demo 2), or **inject** the fact as context (demo 3). Tool calling is for things that change and have to be fetched live, like weather. Injection is for cheap static facts, like today's date.

## Where MCP fits (concept, not built here)

Two tools are easy. Real systems have dozens: calendar, CRM, database, email, files. With the approach here, you hand-wire every one — write the schema, write the function, register it, keep the description in sync. Fifty tools across five apps that keep changing? A maintenance nightmare.

**MCP (Model Context Protocol)** is the open standard that fixes this. Think USB-C for AI tools: one standard plug instead of a custom cable per device. A tool lives behind an MCP server that *describes itself* — here are my tools, here's what each does, here are the arguments. Your app (the MCP client) asks "what have you got?" and discovers the tools at runtime instead of you wiring them in ahead of time. Tools become plug-ins instead of custom code.

We don't build an MCP server here — that's a bigger topic for later. Tool calling is how one model uses a tool; MCP is the standard that lets any model use any tool without gluing them together by hand.

## Setup

From the repo root (one level up from this folder):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

You also need:

- AWS credentials configured (`aws configure` or an SSO profile — run `aws sso login` if your token has expired)
- Amazon Bedrock **model access** enabled for `us.anthropic.claude-haiku-4-5-20251001-v1:0` in `us-east-1`

The weather calls use [Open-Meteo](https://open-meteo.com/), which needs no API key and does city-name geocoding. The date/time tool uses only Python's standard library. So there's no extra dependency for either tool.

## Files

`weather.py` and `datetime_tool.py` hold the two real tool functions — plain
code, no AI. Each demo is **self-contained**: it defines its own tool schema,
Bedrock client, and the loop inline, so you can read one file top to bottom
without jumping around.

```
ep07-tool-calling/
├── weather.py             # Tool 1: current weather. Plain code, no AI. Open-Meteo, no API key.
├── datetime_tool.py       # Tool 2: current date/time. Plain code, standard library only.
│
├── tool_calling_demo.py    # ONE TOOL:  the four steps as a straight line (easiest to walk through)
├── two_tools_demo.py       # TWO TOOLS: the same four steps inside a loop
└── date_injection_demo.py  # NO DATE TOOL: date injected via system prompt (how the apps do it)
```

## Model used

| Step | Model | Why |
|------|-------|-----|
| Reason + tool calls | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | Fast, cheap, supports tool use — good for on-camera pacing |

Runs in `us-east-1`. Switch regions or models by editing the `MODEL` and `REGION` constants at the top of each demo file.

## Questions to try

- **One tool, works:** `"What's the weather in Tokyo right now?"` (edit `QUESTION` in `tool_calling_demo.py`)
- **One tool, hits the limit:** `"What's today's date?"` in `tool_calling_demo.py` — no date tool, so it can't.
- **Two tools:** `"What day is it and what's the weather in London?"` in `two_tools_demo.py` — watch it call both.
- **Injection:** `date_injection_demo.py` — the date answered with no tool call, straight from the system prompt.

## What's next

Today the model called a tool or two, once each, and answered. Episode 8 asks: what if a question needs several tools, in the right order, and the model has to plan, act, look at the result, and decide the next step — over and over? That loop has a name: an agent. We build one with [Strands Agents SDK](https://strandsagents.com/?trk=44b16281-e090-49b6-97d8-f1cea54d9e87&sc_channel=el). [Ride along](https://youtube.com/@RohiniGaonkar).
