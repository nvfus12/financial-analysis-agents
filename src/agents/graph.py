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
from src.infrastructure.config import Config

logger = logging.getLogger(__name__)

# --- Routing functions for sequential task execution ---

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

# --- Graph Builder ---

def build_graph():
    """
    Builds and compiles the multi-agent reasoning StateGraph.
    Integrates persistent SQLite state checkpointer for session/history tracking.
    """
    # Initialize graph with AgentState schema
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("fundamental", fundamental_node)
    workflow.add_node("technical", technical_node)
    workflow.add_node("sentiment", sentiment_node)
    workflow.add_node("synthesis", synthesis_node)

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

    # Sentiment always goes to Synthesis
    workflow.add_edge("sentiment", "synthesis")
    
    # Synthesis terminates the workflow
    workflow.add_edge("synthesis", END)

    # Connect persistent SQLite Checkpointer (WAL mode enabled via database factory)
    db_path = Config.get_db_path()
    logger.info(f"Connecting LangGraph SQLiteSaver checkpointer to: {db_path}")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)
    
    compiled_graph = workflow.compile(checkpointer=memory)
    return compiled_graph
