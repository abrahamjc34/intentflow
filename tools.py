"""
tools.py
--------
Defines the @tool decorator and registers every callable "skill" in IntentFlow.

How it works:
1. `TOOL_REGISTRY` is a plain Python dict — our plugin database.
2. The `@tool(...)` decorator wraps a function and adds it to that dict.
3. The FastAPI router looks up tools in this registry by name.

Adding a new tool is exactly 1 decorator + 1 function. That's the pitch.
"""

from datetime import datetime

# The global registry — { "tool_name": { "fn": <function>, "description": str } }
TOOL_REGISTRY = {}


def tool(name: str, description: str):
    """
    Decorator factory. Usage:

        @tool(name="greet", description="Greets the user")
        def greet(name: str = "friend") -> str:
            return f"Hello, {name}!"

    When Python sees @tool(...), it calls this function, which returns
    the `decorator` below. `decorator` then receives the actual function
    (e.g. `greet`), registers it, and returns it unchanged.
    """
    def decorator(fn):
        TOOL_REGISTRY[name] = {
            "fn": fn,
            "description": description,
        }
        return fn
    return decorator


# ---------------------------------------------------------------------------
# Built-in tools. Add your own below — the @tool decorator does the rest.
# ---------------------------------------------------------------------------

@tool(name="calculator", description="Evaluates a math expression like '25 * 40' or '(5 + 3) / 2'")
def calculator(expression: str) -> str:
    """Evaluate a math expression safely (no builtins, no names)."""
    try:
        # Stripped-down eval: no builtins, no globals, no names.
        result = eval(expression, {"__builtins__": {}}, {})
        return f"The answer is {result}"
    except Exception as e:
        return f"Couldn't compute that: {e}"


@tool(name="current_time", description="Returns the current date and time")
def current_time() -> str:
    now = datetime.now()
    return f"It is currently {now.strftime('%A, %B %d, %Y at %I:%M %p')}"


@tool(name="greet", description="Greets the user by name")
def greet(name: str = "friend") -> str:
    name = name.strip() or "friend"
    return f"Hello, {name.title()}! Welcome to IntentFlow."


@tool(name="reverse", description="Reverses a piece of text")
def reverse(text: str) -> str:
    text = text.strip()
    if not text:
        return "Give me something to reverse!"
    return f"Reversed: {text[::-1]}"


@tool(name="word_count", description="Counts words in a given piece of text")
def word_count(text: str) -> str:
    text = text.strip()
    if not text:
        return "No text provided."
    count = len(text.split())
    return f"That text has {count} word{'s' if count != 1 else ''}."


@tool(name="list_tools", description="Lists every tool available in IntentFlow")
def list_tools() -> str:
    lines = [f"- {name}: {meta['description']}" for name, meta in TOOL_REGISTRY.items()]
    return "Available tools:\n" + "\n".join(lines)
