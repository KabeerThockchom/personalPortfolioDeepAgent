"""Agent Memory Middleware for long-term persistent instructions and knowledge."""

from collections.abc import Awaitable, Callable
from typing import NotRequired, Any
from deepagents.backends.protocol import BackendProtocol

# Import from deepagents core
try:
    from deepagents.middleware import AgentMiddleware
    from deepagents.types import AgentState, ModelRequest, ModelResponse, Runtime
except ImportError:
    # Fallback for different deepagents versions
    from typing import TypedDict

    class AgentState(TypedDict, total=False):
        """Base agent state."""
        pass

    class ModelRequest:
        """Model request wrapper."""
        def __init__(self, state, system_prompt=None):
            self.state = state
            self.system_prompt = system_prompt

    class ModelResponse:
        """Model response wrapper."""
        pass

    class Runtime:
        """Runtime context."""
        pass

    class AgentMiddleware:
        """Base middleware class."""
        state_schema = AgentState

        def before_agent(self, state, runtime):
            pass

        async def abefore_agent(self, state, runtime):
            pass

        def after_agent(self, state, runtime):
            pass

        async def aafter_agent(self, state, runtime):
            pass

        def before_model(self, state, runtime):
            pass

        async def abefore_model(self, state, runtime):
            pass

        def after_model(self, state, runtime):
            pass

        async def aafter_model(self, state, runtime):
            pass

        def wrap_model_call(self, request, handler):
            return handler(request)

        async def awrap_model_call(self, request, handler):
            return await handler(request)

        def wrap_tool_call(self, request, handler):
            return handler(request)

        async def awrap_tool_call(self, request, handler):
            return await handler(request)

class AgentMemoryState(AgentState):
    """State schema with agent_memory field."""
    agent_memory: NotRequired[str | None]

AGENT_MEMORY_FILE_PATH = "/agent.md"

LONGTERM_MEMORY_SYSTEM_PROMPT = """
## Long-term Memory

You have access to a long-term memory system using the {memory_path} prefix.
Files stored here persist across sessions and conversations.

Your system prompt is loaded from {memory_path}agent.md at startup.
You can update your own instructions by editing this file.

**When to CHECK memories (do this FIRST):**
- At the start of new sessions: Run `ls {memory_path}` to see what you know
- Before answering questions: Check for relevant saved knowledge
- When user references past work: Search {memory_path} for context

**Memory-first response pattern:**
1. User asks question → Run `ls {memory_path}` to check for relevant files
2. If relevant files exist → Read them with `read_file '{memory_path}[filename]'`
3. Base answer on saved knowledge (from memories) + general knowledge
4. If no memories exist → Use general knowledge, consider if worth saving

**When to UPDATE memories:**
- IMMEDIATELY when user describes your role or behavior
- IMMEDIATELY when user gives feedback - capture what was wrong and how to improve
- When user explicitly asks you to remember something
- When patterns or preferences emerge
- After significant work where context would help future sessions

**Learning from feedback:**
- Capture WHY something is better/worse as a pattern
- Each correction = chance to improve permanently
- Look for underlying principles, not just specific mistakes

**What to store where:**
- {memory_path}agent.md: Core instructions and behavioral patterns
- Other {memory_path} files: Project context, reference info, structured notes
  - Add references to them in agent.md so you remember to consult them

Example: `ls '{memory_path}'` to see memories
Example: `read_file '{memory_path}investment_philosophy.md'` to recall knowledge
Example: `edit_file('{memory_path}agent.md', old_string, new_string)` to update instructions
"""

DEFAULT_MEMORY_SNIPPET = """<agent_memory>
{agent_memory}
</agent_memory>
"""


class AgentMemoryMiddleware(AgentMiddleware):
    """
    Load agent memory from agent.md and inject into system prompt.

    This middleware:
    1. Loads {memory_path}agent.md at startup
    2. Injects it into the system prompt wrapped in <agent_memory> tags
    3. Adds instructions on how to use long-term memory

    The agent can then:
    - Read its own instructions from memory
    - Update its own instructions by editing agent.md
    - Store long-term knowledge in /memories/ directory
    - Learn from feedback across sessions
    """

    name = "AgentMemoryMiddleware"
    state_schema = AgentMemoryState

    def __init__(
        self,
        *,
        backend: BackendProtocol,
        memory_path: str,
        system_prompt_template: str | None = None,
    ):
        """
        Initialize the AgentMemoryMiddleware.

        Args:
            backend: Backend for file storage (must have agent.md at root)
            memory_path: Path prefix for memory files (e.g., "/memories/")
            system_prompt_template: Template for injecting memory (default: DEFAULT_MEMORY_SNIPPET)
        """
        self.backend = backend
        self.memory_path = memory_path
        self.system_prompt_template = system_prompt_template or DEFAULT_MEMORY_SNIPPET

    def before_agent(self, state: AgentMemoryState, runtime: Runtime):
        """Load agent memory before agent execution."""
        if "agent_memory" not in state or state.get("agent_memory") is None:
            try:
                file_data = self.backend.read(AGENT_MEMORY_FILE_PATH)
                return {"agent_memory": file_data}
            except Exception:
                # If agent.md doesn't exist, use empty string
                return {"agent_memory": ""}

    async def abefore_agent(self, state: AgentMemoryState, runtime: Runtime):
        """Async version of before_agent."""
        if "agent_memory" not in state or state.get("agent_memory") is None:
            try:
                file_data = self.backend.read(AGENT_MEMORY_FILE_PATH)
                return {"agent_memory": file_data}
            except Exception:
                # If agent.md doesn't exist, use empty string
                return {"agent_memory": ""}

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Inject agent memory into system prompt."""
        agent_memory = request.state.get("agent_memory", "")

        # Add memory section
        memory_section = self.system_prompt_template.format(agent_memory=agent_memory)
        if request.system_prompt:
            request.system_prompt = memory_section + "\n\n" + request.system_prompt
        else:
            request.system_prompt = memory_section

        # Add long-term memory instructions
        request.system_prompt = (
            request.system_prompt
            + "\n\n"
            + LONGTERM_MEMORY_SYSTEM_PROMPT.format(memory_path=self.memory_path)
        )

        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """Async version of wrap_model_call."""
        agent_memory = request.state.get("agent_memory", "")

        # Add memory section
        memory_section = self.system_prompt_template.format(agent_memory=agent_memory)
        if request.system_prompt:
            request.system_prompt = memory_section + "\n\n" + request.system_prompt
        else:
            request.system_prompt = memory_section

        # Add long-term memory instructions
        request.system_prompt = (
            request.system_prompt
            + "\n\n"
            + LONGTERM_MEMORY_SYSTEM_PROMPT.format(memory_path=self.memory_path)
        )

        return await handler(request)
