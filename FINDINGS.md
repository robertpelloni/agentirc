# AgentIRC Technical Findings & Analysis

## 1. Python 3.14.3 "Hardening"
Operating on the experimental Python 3.14.3 runtime revealed several critical breaking changes in the `asyncio` and `anyio` ecosystems.

### Findings:
- **Strict Task Context**: Python 3.14 enforces a valid `asyncio.Task` context for operations like `asyncio.wait_for` and `asyncio.timeouts`. 
- **The EngineIO Clash**: `engineio` (used by Chainlit) runs service loops in background threads/loops that lack formal task registration. This previously resulted in `RuntimeError: Timeout should be used inside a task`.
- **AnyIO Identity Mismatch**: `anyio`'s `CancelScope` tracks the "host task" using weak references. On Python 3.14, if the task is `None`, this triggers a `TypeError: cannot create weak reference to 'NoneType' object`.

### Solutions (The "Task Identity Lie"):
We implemented a multi-layered bootstrapper in `run.py`:
1. **Singleton Dummy Task**: Created a `GLOBAL_DUMMY_TASK` class that mimics the minimum `asyncio.Task` interface (`cancelling()`, `uncancel()`) and is weak-referencable.
2. **Context Synchronization**: Patched `anyio._backends._asyncio.CancelScope.__enter__` and `__exit__` to forcibly synchronize `_host_task` with the current context (even if it's our dummy task).
3. **State Machine Repair**: Patched `asyncio.timeouts.Timeout` to manually transition state to `ENTERED` if the native enter fails, preventing subsequent `AssertionError` during cleanup.

## 2. AutoGen 0.4 (Modular) Migration
This project successfully migrated from the legacy `pyautogen` (0.2.x) to the modular `autogen-agentchat` (0.4+) API.

### Findings:
- **Identifier Consistency**: Agent names must now be valid Python identifiers (e.g., `GPT_5` instead of `GPT-5`). Failure to comply causes a `ValueError`.
- **Event-Driven UI**: Used the `run_stream` API to capture `ChatMessage` and `AgentEvent` objects. This allows for native asynchronous UI updates without blocking the main event loop.
- **Subscripted Generic Limitation**: Modern Python versions prohibit `isinstance()` checks on subscripted generics (like `ChatMessage`). We pivoted to robust attribute-based detection (`hasattr(event, "content")`).

## 3. Interaction Design: Broadcast vs. Discussion
We evolved the interaction from a simple sequential broadcast to a dynamic state-managed system.

### Dynamic Team Re-initialization
The project implements a `create_team` factory that handles the transition between two distinct AutoGen team architectures without losing session context:
- **Broadcast Mode (`RoundRobinGroupChat`)**: Uses `MaxMessageTermination` to ensure a one-to-one response ratio per user prompt.
- **Discussion Mode (`SelectorGroupChat`)**: Uses a dual termination (`TextMentionTermination` OR `MaxMessageTermination(10)`) to allow agents to debate a topic autonomously for a limited duration.

### IRC Command Parsing
A custom command parser was implemented in `cl.on_message`:
- **Stateful Topic Control**: `/topic <text>` updates the `cl.user_session` and re-injects the new focus into the system messages of all agents via the factory.
- **Targeted Pings**: Support for `@AgentName` allows the user to bypass the team logic and prompt a single model directly, while still maintaining the overall IRC transcript.

### 4. UI/UX Aesthetic & Logging
- **Persistent Archival**: All IRC traffic is piped to `irc_session.log`. This ensures that even experimental "future-edition" debates are preserved for the Omni-Workspace knowledge base.
- **Monospace Hardening**: Enforced `Courier New` and dark themes via both `config.toml` and custom CSS injection to satisfy the "Hacker" aesthetic requirements.
