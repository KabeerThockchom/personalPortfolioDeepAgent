"""Token calculation utilities using model's official tokenizer."""

from pathlib import Path
from langchain_core.messages import SystemMessage
from src.config import console, COLORS


def calculate_baseline_tokens(model, agent_dir: Path, system_prompt: str) -> int:
    """
    Calculate baseline context tokens using model's tokenizer.

    Uses model.get_num_tokens_from_messages() for accuracy.
    Tools are not counted (added after first API call, ~5k tokens).

    Args:
        model: The LLM model instance with get_num_tokens_from_messages method
        agent_dir: Path to agent directory containing agent.md
        system_prompt: The main system prompt text

    Returns:
        Token count for system prompt + agent.md (tools excluded)
    """
    # Load agent.md
    agent_md_path = agent_dir / "agent.md"
    agent_memory = ""
    if agent_md_path.exists():
        try:
            agent_memory = agent_md_path.read_text()
        except Exception as e:
            console.print(f"[{COLORS['warning']}]Warning: Could not read agent.md: {e}[/{COLORS['warning']}]")

    # Build complete system prompt (matches AgentMemoryMiddleware)
    memory_section = f"<agent_memory>\n{agent_memory}\n</agent_memory>"
    full_system_prompt = memory_section + "\n\n" + system_prompt

    messages = [SystemMessage(content=full_system_prompt)]

    try:
        # Use model's official tokenizer
        token_count = model.get_num_tokens_from_messages(messages)
        return token_count
    except Exception as e:
        console.print(f"[{COLORS['warning']}]Warning: Could not calculate tokens: {e}[/{COLORS['warning']}]")
        # Fallback: rough estimate (4 chars per token)
        return len(full_system_prompt) // 4
