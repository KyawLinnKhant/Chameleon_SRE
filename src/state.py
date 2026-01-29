"""
State management for LangGraph agent
Defines the memory structure that persists across reasoning loops
"""

from typing import List, TypedDict, Annotated
from operator import add


class AgentState(TypedDict):
    """
    State that persists across agent reasoning iterations
    
    This is the "memory" of the agent - it accumulates context
    as it loops through Think → Act → Observe cycles
    """
    
    # Conversation history (messages from user and agent)
    messages: Annotated[List[dict], add]
    
    # Current task the agent is working on
    current_task: str
    
    # Kubernetes cluster state snapshot
    cluster_state: dict
    
    # Error log from failed operations
    error_log: List[str]
    
    # Number of iterations in current reasoning loop
    iteration_count: int
    
    # Flag to indicate if task is complete
    task_complete: bool
    
    # Last tool output (for verification loops)
    last_tool_output: str
    
    # RAG search results
    knowledge_context: List[dict]


def create_initial_state(user_input: str) -> AgentState:
    """
    Initialize agent state for a new task
    
    Args:
        user_input: The user's request/query
    
    Returns:
        Fresh AgentState with default values
    """
    return AgentState(
        messages=[{"role": "user", "content": user_input}],
        current_task=user_input,
        cluster_state={},
        error_log=[],
        iteration_count=0,
        task_complete=False,
        last_tool_output="",
        knowledge_context=[]
    )


def should_continue(state: AgentState, max_iterations: int = 10) -> bool:
    """
    Determine if the agent should continue reasoning loop
    
    Args:
        state: Current agent state
        max_iterations: Maximum allowed iterations
    
    Returns:
        True if agent should continue, False if should stop
    """
    if state["task_complete"]:
        return False
    
    if state["iteration_count"] >= max_iterations:
        return False
    
    # Stop if too many consecutive errors
    if len(state["error_log"]) >= 5:
        return False
    
    return True


def format_state_for_display(state: AgentState) -> str:
    """
    Format state into human-readable string for debugging
    
    Args:
        state: Current agent state
    
    Returns:
        Formatted string representation
    """
    output = []
    output.append("=" * 60)
    output.append(f"Task: {state['current_task']}")
    output.append(f"Iteration: {state['iteration_count']}")
    output.append(f"Complete: {state['task_complete']}")
    
    if state["error_log"]:
        output.append(f"Errors: {len(state['error_log'])}")
        output.append("  " + "\n  ".join(state["error_log"][-3:]))  # Last 3 errors
    
    if state["knowledge_context"]:
        output.append(f"Knowledge Articles: {len(state['knowledge_context'])}")
    
    output.append("=" * 60)
    
    return "\n".join(output)
