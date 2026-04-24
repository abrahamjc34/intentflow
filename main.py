"""
main.py
-------
The FastAPI application for IntentFlow, a multi-agent system.

Endpoints:
  GET  /          health + registered tools + agent status
  GET  /tools     every @tool-registered function and its description
  GET  /intents   every intent loaded from intents/intents.md
  POST /chat      (single-agent baseline) intent-route -> tool
  POST /agent     (multi-agent pipeline) Security -> Planner -> Executor -> Critic
  GET  /ui        static chat frontend (from ./static/index.html)

Run with:
    uvicorn main:app --reload
"""

from typing import Optional, Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from tools import TOOL_REGISTRY
from router import load_intents, match_intent, extract_argument
from agents import run_multi_agent

app = FastAPI(
    title="IntentFlow Multi-Agent System",
    description=(
        "A multi-agent system built on FastAPI. Four specialized agents "
        "(Security, Planner, Executor, Critic) collaborate to safely answer "
        "user requests, combining deterministic tool calls with LLM reasoning."
    ),
    version="2.0.0",
)

# Let the browser chat UI call the API freely.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load intents once at startup.
INTENTS = load_intents()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    intent: Optional[str] = None
    tool: Optional[str] = None
    args: dict = {}
    reply: str


class AgentRequest(BaseModel):
    message: str


class AgentResponse(BaseModel):
    reply: str
    trace: Dict[str, Any] = {}


@app.get("/")
def root():
    return {
        "status": "IntentFlow multi-agent system is running",
        "agents": ["SecurityAgent", "PlannerAgent", "ExecutorAgent", "CriticAgent"],
        "tools": list(TOOL_REGISTRY.keys()),
        "intents_loaded": len(INTENTS),
    }


@app.get("/tools")
def list_registered_tools():
    """Show every function that was decorated with @tool."""
    return {name: meta["description"] for name, meta in TOOL_REGISTRY.items()}


@app.get("/intents")
def list_registered_intents():
    """Show every intent parsed from intents/intents.md."""
    return INTENTS


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Single-agent baseline: keyword-route -> tool. Kept for comparison."""
    intent = match_intent(req.message, INTENTS)
    if not intent:
        return ChatResponse(
            intent=None,
            tool=None,
            args={},
            reply="Sorry, I didn't understand that. Try asking 'what can you do?'",
        )

    tool_meta = TOOL_REGISTRY.get(intent["tool"])
    if not tool_meta:
        raise HTTPException(
            status_code=500,
            detail=f"Intent '{intent['name']}' points to tool '{intent['tool']}' but that tool isn't registered.",
        )

    args = extract_argument(req.message, intent)

    try:
        result = tool_meta["fn"](**args) if args else tool_meta["fn"]()
    except TypeError:
        result = tool_meta["fn"]()
    except Exception as e:
        result = f"Tool '{intent['tool']}' errored: {e}"

    return ChatResponse(
        intent=intent["name"],
        tool=intent["tool"],
        args=args,
        reply=str(result),
    )


@app.post("/agent", response_model=AgentResponse)
def agent(req: AgentRequest):
    """The multi-agent endpoint: Security -> Planner -> Executor -> Critic.

    Returns the final reply plus a full audit trace of every agent's output —
    useful for demos, debugging, and accountability.
    """
    result = run_multi_agent(req.message)
    return AgentResponse(**result)


# Serve the static demo UI at /ui (must be mounted AFTER the API routes).
app.mount("/ui", StaticFiles(directory="static", html=True), name="ui")
