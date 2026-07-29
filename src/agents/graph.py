import sqlite3
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from src.domain.models.state import AgentState
from src.agents.nodes.orchestrator import orchestrator_node
from src.agents.nodes.fundamental import fundamental_node
from src.agents.nodes.technical import technical_node
from src.agents.nodes.sentiment import sentiment_node
from src.agents.nodes.synthesis import synthesis_node
from src.agents.nodes.critic import critic_node
from src.infrastructure.config import Config

logger = logging.getLogger(__name__)

# --- Routing functions for sequential task execution & smart reflection ---

def route_after_orchestrator(state: AgentState) -> str:
    raw = state.get("raw_financials", {})
    planned = raw.get("planned_nodes", [])
    
    if "fundamental" in planned:
        return "fundamental"
    elif "technical" in planned:
        return "technical"
    elif "sentiment" in planned:
        return "sentiment"
    return "synthesis"

def route_after_fundamental(state: AgentState) -> str:
    raw = state.get("raw_financials", {})
    planned = raw.get("planned_nodes", [])
    
    if "technical" in planned:
        return "technical"
    elif "sentiment" in planned:
        return "sentiment"
    return "synthesis"

def route_after_technical(state: AgentState) -> str:
    raw = state.get("raw_financials", {})
    planned = raw.get("planned_nodes", [])
    
    if "sentiment" in planned:
        return "sentiment"
    return "synthesis"

def route_after_critic(state: AgentState) -> str:
    passed = state.get("critic_passed", True)
    count = state.get("reflection_count", 0)
    failed_node = state.get("failed_node", "synthesis")
    
    # If audit failed AND max reflection limit (< 2) not reached -> Route to exact failed node
    if not passed and count < 2:
        logger.info(f"[Smart Reflection] Routing back to failed node '{failed_node}' (Attempt #{count}).")
        return failed_node
        
    return END

# --- Graph Builder ---

def build_graph():
    """
    Builds and compiles the multi-agent reasoning StateGraph.
    Integrates persistent SQLite state checkpointer for session/history tracking,
    and smart reflection self-correction loop.
    """
    # Initialize graph with AgentState schema
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("fundamental", fundamental_node)
    workflow.add_node("technical", technical_node)
    workflow.add_node("sentiment", sentiment_node)
    workflow.add_node("synthesis", synthesis_node)
    workflow.add_node("critic", critic_node)

    # Set Entry Point
    workflow.add_edge(START, "orchestrator")

    # Add Routing Edges
    workflow.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "fundamental": "fundamental",
            "technical": "technical",
            "sentiment": "sentiment",
            "synthesis": "synthesis"
        }
    )

    workflow.add_conditional_edges(
        "fundamental",
        route_after_fundamental,
        {
            "technical": "technical",
            "sentiment": "sentiment",
            "synthesis": "synthesis"
        }
    )

    workflow.add_conditional_edges(
        "technical",
        route_after_technical,
        {
            "sentiment": "sentiment",
            "synthesis": "synthesis"
        }
    )

    # Sentiment connects to Synthesis
    workflow.add_edge("sentiment", "synthesis")
    
    # Synthesis connects to Critic Auditor
    workflow.add_edge("synthesis", "critic")

    # Critic routes dynamically back to failed node or END
    workflow.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "fundamental": "fundamental",
            "technical": "technical",
            "sentiment": "sentiment",
            "synthesis": "synthesis",
            END: END
        }
    )

    # Connect persistent SQLite Checkpointer (WAL mode enabled via database factory)
    db_path = Config.get_db_path()
    logger.info(f"Connecting LangGraph SQLiteSaver checkpointer to: {db_path}")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)
    
    compiled_graph = workflow.compile(checkpointer=memory)
    return compiled_graph
