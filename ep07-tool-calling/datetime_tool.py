"""
The second tool — Episode 7
===========================
Plain, boring code. No AI in it.

`get_current_datetime()` returns the current date and time. This is the tool
the model calls when you ask "what's today's date?" — but ONLY if you give it
this tool. The model, on its own, has no idea what day it is. Its knowledge is
frozen at training time (callback to Episode 2).

There are two ways to hand the model the current date:
  1. Give it a tool, like this one, and let it ask. (What we do here.)
  2. Slip the date into the system prompt as plain text. (What the chat apps
     do — see date_injection_demo.py.)

This file is option 1. Same pattern as weather.py: the model never runs this
function directly. It only asks us to, and our code does the work.
"""

from datetime import datetime, timezone


def get_current_datetime() -> dict:
    """
    Return the current date and time.

    Example:
      {"date": "2026-07-27", "day_of_week": "Monday", "time": "14:05",
       "utc": "2026-07-27T18:05:00Z",
       "note": "Local time of the machine running this tool."}

    Takes no arguments — there's nothing to look up but "now".
    """
    now_local = datetime.now()
    now_utc = datetime.now(timezone.utc)
    return {
        "date": now_local.strftime("%Y-%m-%d"),
        "day_of_week": now_local.strftime("%A"),
        "time": now_local.strftime("%H:%M"),
        "utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": "Local time of the machine running this tool.",
    }


# Run this file directly to confirm the tool works BEFORE the shoot.
#   python3 datetime_tool.py
if __name__ == "__main__":
    print(f"get_current_datetime() ->")
    print(f"  {get_current_datetime()}")
