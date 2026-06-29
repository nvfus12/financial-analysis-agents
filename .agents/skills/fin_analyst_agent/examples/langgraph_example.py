from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# 1. Define Graph State
class ExampleState(TypedDict):
    ticker: str
    analysis_mode: str
    data: Dict[str, Any]
    report: str
    logs: List[str]

# 2. Define Node Functions
def gather_data_node(state: ExampleState) -> Dict[str, Any]:
    print(f"--- Node 1: Gathering data for {state['ticker']} ---")
    # Returns dictionary of fields to update in State
    return {
        "data": {"price": 120.5, "pe": 15.2},
        "logs": state.get("logs", []) + ["[Data Node] Fetched price and P/E ratios."]
    }

def generate_report_node(state: ExampleState) -> Dict[str, Any]:
    print(f"--- Node 2: Generating Report ---")
    ticker = state["ticker"]
    price = state["data"].get("price")
    pe = state["data"].get("pe")
    report = f"Stock Report for {ticker}:\n- Current Price: {price}\n- P/E Ratio: {pe}"
    return {
        "report": report,
        "logs": state.get("logs", []) + ["[Report Node] Created final markdown report."]
    }

# 3. Define Conditional Routing Logic
def route_after_data(state: ExampleState) -> str:
    # Router returns the name of the next node to execute
    if state["analysis_mode"] == "full":
        return "generate_report"
    return END

# 4. Build and Compile the Graph
def build_graph():
    # Initialize Graph with Schema
    workflow = StateGraph(ExampleState)

    # Add Nodes
    workflow.add_node("gather_data", gather_data_node)
    workflow.add_node("generate_report", generate_report_node)

    # Set Entry Point
    workflow.add_edge(START, "gather_data")

    # Add Conditional Edges
    workflow.add_conditional_edges(
        "gather_data",
        route_after_data,
        {
            "generate_report": "generate_report",
            END: END
        }
    )

    # Normal Edge (Direct connection)
    workflow.add_edge("generate_report", END)

    # Compile with Memory Checkpointer (for session tracking)
    memory = MemorySaver()
    compiled_graph = workflow.compile(checkpointer=memory)
    return compiled_graph

if __name__ == "__main__":
    # Test execution
    graph = build_graph()
    initial_state = {
        "ticker": "FPT",
        "analysis_mode": "full",
        "logs": []
    }
    
    # Run with configuration (thread_id for session tracking)
    config = {"configurable": {"thread_id": "session_1"}}
    final_state = graph.invoke(initial_state, config)
    
    print("\n--- Final Report Output ---")
    print(final_state["report"])
    print("\n--- Execution Logs ---")
    print(final_state["logs"])
