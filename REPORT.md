# IntentFlow — A Multi-Agent System for Safe, Accurate Task Execution

**Author:** Jacob Abraham
**Submitted:** April 23, 2026
**Repository:** https://github.com/abrahamjc34/intentflow

**Use case.** IntentFlow is a secure, general-purpose AI assistant: the user sends a natural-language request (a question, a calculation, a multi-step lookup), and the system returns a validated answer. The interesting engineering is not the task itself but *how* the task is executed — every request passes through four specialized agents that enforce security, decompose the problem, prefer deterministic tools over LLM reasoning, and validate the final output. The design is directly applicable to customer support, internal developer assistants, and information-retrieval front-ends, all of which need the same combination of task decomposition, tool use, and output validation.

## 1. Multi-Agent Architecture

IntentFlow is a four-agent system that accepts a natural-language user request and returns a validated answer. Agents run **sequentially**, in a pipeline, each receiving a structured message from the previous agent:

```
User -> SecurityAgent -> PlannerAgent -> ExecutorAgent -> CriticAgent -> User
```

**Agents and responsibilities.** The **SecurityAgent** is the first line of defense — it applies regex-based prompt-injection detection, PII redaction (SSN, card-number patterns), and input-size limits before any downstream agent sees the request. The **PlannerAgent** is an LLM-powered planner that decomposes the sanitized request into 1–4 ordered subtasks, returning structured JSON. The **ExecutorAgent** runs each subtask; it first attempts to match the subtask to a deterministic `@tool`-decorated Python function (calculator, current_time, reverse, word_count, etc.), and only falls back to LLM reasoning when no tool applies. The **CriticAgent** is an LLM-powered reviewer that inspects the assembled draft, approves or rewrites it, and produces the final answer.

**Communication pattern.** Each agent emits a structured Python dict that is appended to a shared audit trace. The orchestrator in `agents.run_multi_agent` passes state forward explicitly — no hidden global memory — which makes every decision inspectable.

**Boundaries.** No agent may call another agent directly; all coordination is handled by the orchestrator. Tool calls are confined to the Executor. LLM access is confined to the Planner, Executor (fallback), and Critic. This prevents unintended escalation: the Security layer cannot be bypassed by a later agent, and tools cannot be invoked without passing the Planner's JSON schema.

## 2. Security, Safety, and Guardrails

The SecurityAgent enforces **four classes of guardrail** before any LLM call is made. **(1) Prompt injection defense:** a regex corpus covers common attack patterns ("ignore previous instructions", "act as…", fake system tags). Matches are rejected with an explanation rather than silently stripped. **(2) PII redaction:** Social Security and card-number patterns are replaced with `[REDACTED-SSN]` / `[REDACTED-CARD]` tokens and logged in the trace. **(3) Input size limits:** 2,000 characters max to bound LLM cost and limit attack surface. **(4) Structured-output constraints:** the Planner and Critic are forced into JSON-only output via Groq's `response_format={"type": "json_object"}`, preventing free-form escape.

**Secret handling.** The Groq API key is loaded from a `.env` file that is excluded from git via `.gitignore`; it never enters the repository or the client.

**Failure isolation.** Every LLM call is wrapped in `try/except`. A parse failure in the Planner degrades to "treat the whole request as one subtask". A failure in the Critic passes the Executor's draft through unmodified rather than crashing the pipeline. This is a deliberate trade-off — availability over strictness — appropriate for a demo; a production version would fail closed on Critic error.

## 3. Implementation Approach

**Stack.** Python 3.9+, FastAPI for HTTP, Pydantic for request/response schemas, Groq's `llama-3.3-70b-versatile` as the LLM (free tier, OpenAI-compatible API), and a custom `@tool` decorator + markdown-based intent registry for the deterministic tool layer. Deliberately **no LangChain, AutoGen, or CrewAI** — the orchestration is ~200 lines of explicit Python, which makes every agent boundary visible and auditable.

**Agent lifecycle.** Agents are stateless class methods. The orchestrator instantiates each agent's call on demand, passes the output forward, and discards intermediate state after the response is returned. There is no long-lived agent memory — each request is independent, which simplifies reasoning about security and bounds the blast radius of any single bug.

**Error handling and retries.** Every LLM call flows through a single `_llm_call` helper that retries once on transient failure with exponential backoff (0.5s, then 1s) before raising. Tool errors fall through to LLM reasoning. LLM parse errors fall through to safe defaults — the Planner degrades to a single-subtask plan, the Critic passes the Executor's draft through unchanged. Every failure, retry, and fallback is written to a structured log file (`logs/intentflow.log`) and reflected in the `trace` returned to the client.

**Evaluation.** The `tests/test_agents.py` module provides two tiers of coverage: nine deterministic unit tests of the SecurityAgent (always run, no network) and three integration tests that exercise the full pipeline against the real LLM (only run when `GROQ_API_KEY` is set). The `/agent` endpoint also returns both the final `reply` and the full audit `trace` on every request, enabling manual verification of each agent's contribution. A representative test case ("What is 25 times 40?") exercises all four agents and surfaced a real Executor tool-call failure that the Critic successfully corrected — demonstrating the value of the multi-agent design empirically.

## 4. Use of AI / LLMs and Collaboration

LLMs are used at **three distinct decision points**: planning (decomposing a free-form request into structured subtasks), executing (when no deterministic tool matches), and critique (validating and rewriting the final answer). The Security layer uses zero LLM calls — it's pure deterministic regex, because safety gates should not themselves be probabilistic.

**Collaboration.** Agents collaborate through the audit trace rather than direct negotiation: the Planner's output shapes what the Executor attempts; the Executor's result shapes what the Critic reviews. The Critic has the explicit authority to overrule the Executor — in testing, when the calculator tool errored on input "Calculate 25 * 40 using calculator", the Critic agent recognized the failure from context and produced the correct answer "25 times 40 equals 1000".

**Autonomy vs. control trade-offs.** IntentFlow deliberately sits on the **control** end of the spectrum. Agents have narrow responsibilities, are constrained to JSON outputs, and cannot invoke each other. The Executor prefers deterministic tools over LLM reasoning whenever possible, because deterministic behavior is easier to debug, test, and secure. The alternative — a fully autonomous agent graph (e.g. AutoGen) — would be more flexible but far harder to reason about for security review. Given a pre-screening context that weights security and defensibility heavily, constrained pipelining is the right choice.
